# src/services/readers/mail_reader.py
from __future__ import annotations

import imaplib
import email
from email.header import decode_header
import threading
import time
import atexit
import socket
import os
import re
import random
import datetime
from email.utils import parseaddr

from utils.extract import extract_data_from_text
from utils import get_xml, get_cdata
from utils import set_alarms
from utils.logger import LoggerSingleton
from utils.clear_text import get_clean_body
from database import get_alarm_patterns as get_patterns
from database import exception_mail
from database import set_alarms_to_db


logger = LoggerSingleton.get_logger("services.readers.mail_reader")

def _resolve_host_ipv4_first(host: str) -> str:
    if os.getenv("IMAP_FORCE_IPV4", "0") not in ("1", "true", "True"):
        return host
    try:
        infos = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        if infos:
            return infos[0][4][0]  # primera IPv4
    except Exception:
        pass
    return host  # fallback

# =========================
#   Conexión persistente
# =========================
class ImapPersistent:
    """
    Mantiene una única sesión IMAP (plaintext) por proceso.
    Reusa la misma conexión entre ejecuciones y reconecta si está caída.
    """
    _instance: "ImapPersistent | None" = None
    _inst_lock = threading.Lock()

    def __init__(self, usuario: str, clave: str, servidor: str, puerto: int = 143, carpeta: str = "INBOX"):
        self.usuario = usuario
        self.clave = clave
        self.servidor = servidor
        self.puerto = puerto
        self.carpeta = carpeta
        self._conn: imaplib.IMAP4 | None = None
        self._lock = threading.Lock()
        self._selected = None  # nombre de carpeta seleccionada
        self._cooldown_until = 0.0  # epoch hasta la que no reconectar
        self._min_reconnect_interval = float(os.getenv("IMAP_MIN_RECONNECT_SEC", "5"))  # ej. 5s
        self._retries = int(os.getenv("IMAP_RETRIES", "3"))  # intentos de reconexión
        self._backoff_base = float(os.getenv("IMAP_BACKOFF_BASE", "0.6"))  # base exponencial

    @classmethod
    def get(cls, usuario: str, clave: str, servidor: str, puerto: int = 143, carpeta: str = "INBOX") -> "ImapPersistent":
        with cls._inst_lock:
            if cls._instance is None:
                cls._instance = ImapPersistent(usuario, clave, servidor, puerto, carpeta)
            return cls._instance

    def _connect(self) -> imaplib.IMAP4:
        host = _resolve_host_ipv4_first(self.servidor)
        mail = imaplib.IMAP4(host, self.puerto)
        mail.login(self.usuario, self.clave)
        logger.info("IMAP persistente: login OK %s:%s (%s)", host, self.puerto, self.carpeta)
        return mail
    
    def _ensure_selected(self, mail: imaplib.IMAP4):
        if self._selected == self.carpeta:
            return
        typ, _ = mail.select(self.carpeta)
        if typ != "OK":
            raise imaplib.IMAP4.error(f"No se pudo seleccionar {self.carpeta}")
        self._selected = self.carpeta
        logger.debug("IMAP persistente: select '%s' OK", self.carpeta)

    def _noop(self, mail: imaplib.IMAP4):
        # algunos servidores devuelven ('OK', [b''])
        try:
            mail.noop()
        except Exception as e:
            raise imaplib.IMAP4.abort(f"NOOP falló: {e}")

    def ensure_connection(self) -> imaplib.IMAP4:
        """
        Devuelve una conexión lista (logueada + carpeta seleccionada).
        Si detecta caída, aplica cooldown y reintentos con backoff.
        """
        with self._lock:
            # 1) Si hay conexión, prueba salud (NOOP) y select
            try:
                if self._conn is not None:
                    self._noop(self._conn)
                    self._ensure_selected(self._conn)
                    return self._conn
            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
                logger.warning("IMAP persistente: NOOP falló, reconectando: %s", e)
                self._safe_close(self._conn)
                self._conn = None  # fuerza conexión nueva

            # 2) Respeta cooldown entre reconexiones (evita EOF por rate-limit)
            now = time.time()
            if now < self._cooldown_until:
                sleep_for = self._cooldown_until - now
                logger.warning("IMAP persistente: cooldown %.2fs antes de reconectar", sleep_for)
                time.sleep(sleep_for)

            # 3) Reintentos con backoff y jitter
            last_err = None
            for attempt in range(self._retries + 1):
                try:
                    self._conn = self._connect()
                    self._selected = None
                    self._ensure_selected(self._conn)
                    # éxito: limpiar cooldown
                    self._cooldown_until = 0.0
                    return self._conn
                except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
                    last_err = e
                    # backoff exponencial + jitter
                    delay = self._backoff_base * (2 ** attempt) + random.random() * 0.3
                    logger.warning("IMAP persistente: reconexión intento %d/%d falló: %s; esperando %.2fs",
                                   attempt + 1, self._retries + 1, e, delay)
                    time.sleep(delay)

            # 4) Si agotamos intentos, fija cooldown y propaga
            self._cooldown_until = time.time() + max(2 * self._backoff_base, self._min_reconnect_interval)
            logger.error("IMAP persistente: agotados reintentos; próximo intento después de %.1fs",
                         self._cooldown_until - time.time())
            raise imaplib.IMAP4.abort(f"Reconexión fallida tras {self._retries+1} intentos") from last_err

    def close(self):
        with self._lock:
            self._safe_close(self._conn)
            self._conn = None
            self._selected = None

    def _safe_close(self, mail: imaplib.IMAP4 | None):
        if mail is None:
            return
        try:
            # cerrar mailbox antes de logout
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                try:
                    mail.shutdown()
                except Exception:
                    pass
        except Exception:
            # no queremos romper por cierre
            pass


# Cierre al terminar el proceso
def _close_on_exit():
    inst = ImapPersistent._instance
    if inst is not None:
        inst.close()
atexit.register(_close_on_exit)

# =====================================
#   API pública: correr una iteración
# =====================================
def procesar_correo_conexion_persistente(usuario: str, clave: str, servidor: str, puerto: int = 143, carpeta: str = "INBOX"):
    """
    Ejecuta una pasada de lectura usando una conexión persistente.
    Lanza excepción si hay errores (que tu scheduler capturará).
    """
    imap = ImapPersistent.get(usuario, clave, servidor, puerto, carpeta).ensure_connection()
    process_unread_messages(imap)

# =========================
#   Procesamiento mensajes
# =========================
def process_unread_messages(mail: imaplib.IMAP4):
    """Procesa todos los UNSEEN en la carpeta actual."""
    criterio = '(UNSEEN ON 23-Oct-2025")'
    status, mensajes = mail.search(None, criterio)
    if status != "OK":
        logger.warning("Could not search for unread messages")
        return

    ids = mensajes[0].split()
    logger.info("Unread mails: %d", len(ids))
    
    #Get black_list from database
    black_list = exception_mail.get({"_id": "exceptions_email"})
    subject_list = exception_mail.get({"_id": "exceptions_subjects"})

    for num in ids:
        process_single_message(mail, num, black_list, subject_list)

def process_single_message(mail, message_id, blacklist, subject_list):    
    """Process a single email message (robusto ante respuestas diversas de FETCH)."""
    # Asegura tipo aceptable para imaplib
    msg_id = message_id.decode() if isinstance(message_id, (bytes, bytearray)) else str(message_id)

    # Usa PEEK para no marcar \Seen automáticamente
    status, data = mail.fetch(msg_id, "(BODY.PEEK[])")
    if status != "OK" or not data:
        logger.warning("Error getting message ID %s (status=%s, data=%r)", msg_id, status, data)
        return

    raw = _extract_msg_bytes(data)
    if not isinstance(raw, (bytes, bytearray)) or not raw:
        # Loguea tipos para depurar (evita volcar el mensaje)
        kinds = [f"{type(p).__name__}" if not isinstance(p, tuple)
                 else f"tuple({type(p[0]).__name__},{type(p[1]).__name__})"
                 for p in data]
        logger.error("FETCH %s sin payload válido; partes=%s", msg_id, kinds)
        # No marcamos visto para reintentar más tarde
        return

    try:
        mensaje = email.message_from_bytes(raw)
    except Exception:
        logger.exception("Error parseando MIME en msg %s", msg_id)
        # No marcar como visto
        return

    asunto = get_email_subject(mensaje)
    body = get_body_from_email(mensaje)
    de, ip = get_email_sender(mensaje)
    #imprime el remitente en el log
    logger.info("From=%s ", de)
    
    if (blacklist is None  and de.lower() in blacklist.lower()) or (subject_list is not None and any(p.lower() in asunto.lower() for p in subject_list)):
        logger.info("El correo de %s está en la lista negra, se omite su procesamiento.", de)
        mark_message(mail, msg_id, seen=False)
        copy_message_to_date_folder(mail, message_id, "blacklist")
        return
    
    xml = get_xml.extraer_xml(body)
    try:
        if xml:
            cdata_data = get_patterns.get_patterns({"_id": "data_xml"})[0]
            datos_extraidos = get_cdata.extract_cdata(xml, cdata_data)
            if not datos_extraidos:
                logger.warning("Sin datos de CDATA en msg %s (%s)", msg_id, asunto)
                return                    
        else:  # si no es un xml busca en todo lo demas
#                    raise ValueError("No es un XML, se procesa como texto plano")       
            datos_extraidos = extract_data_from_text.extract_data(body)
        if ip:
            datos_extraidos["ip_dispositivo"] = ip
        else:
            if datos_extraidos["ip_dispositivo"] == "Not available":
                ip = get_email_from_name_dvr(datos_extraidos["nombre_dispositivo"])  
                datos_extraidos["ip_dispositivo"] = ip                      
   
        alarm = set_alarms.set_doc_to_alarm(datos_extraidos)
        set_alarms_to_db.save_or_update_alarm(alarm)
        mark_message(mail, msg_id, seen=True)
        copy_message_to_date_folder(mail, message_id)
                    
    except Exception as e:
        logger.exception(f"Error procesando msg {de} - {asunto} - {e}")
        mark_message(mail, msg_id, seen=False)


def get_email_subject(mensaje):
    asunto, encoding = decode_header(mensaje["Subject"])[0]
    if isinstance(asunto, bytes):
        asunto = asunto.decode(encoding or "utf-8", errors="ignore")
    return asunto or "(sin asunto)"

def is_subject_matching(subject, filters):
    return any(str(f).lower() in (subject or "").lower() for f in filters)

def mark_message(mail: imaplib.IMAP4, message_id: bytes, seen=True):
    flag = '+FLAGS' if seen else '-FLAGS'
    mail.store(message_id, flag, '\\Seen')

def get_body_from_email(mensaje):
    if mensaje.is_multipart():
        # prioriza text/plain
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                return get_clean_body(parte)
        # fallback a la primera parte decodificable
        for parte in mensaje.walk():
            if parte.get_content_maintype() == "text":
                return get_clean_body(parte)
        return ""
    else:
        return get_clean_body(mensaje)
    
def get_email_sender(mensaje):
    """
    Devuelve el remitente en formato limpio: 'nombre <correo@dominio>'.
    """
    raw_from = mensaje.get("From", "")
    name, addr = parseaddr(raw_from)
    addr = addr or raw_from
    ip_match = None
    if addr:
        try:
            # Busca patrón de IPv4 antes del @
            m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})@", addr)
            if m:
                ip_match = m.group(1)
        except Exception:
            ip_match = None
    return addr, ip_match

def get_email_from_name_dvr(name: str):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    match = re.search(ip_pattern, name)
    if match:
        return match.group()
    return None

def _extract_msg_bytes(fetch_data):
    """
    Extrae el payload en bytes del resultado de imap.fetch().
    Soporta respuestas con tuplas, bytes sueltos y elementos basura (ints, b')', None).
    """
    if not fetch_data:
        return None

    # 1) Prioriza tuplas (meta, payload)
    for part in fetch_data:
        if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], (bytes, bytearray)):
            return part[1]

    # 2) Si no hubo tuplas válidas, busca bytes sueltos
    for part in fetch_data:
        if isinstance(part, (bytes, bytearray)) and part:
            return part

    # 3) Nada útil → devuelve None
    return None

def copy_message_to_date_folder(mail: imaplib.IMAP4, message_id: bytes, folder_name="Procesados", root_folder="INBOX"):
    """
    Crea una carpeta con la fecha actual (si no existe) y copia ahí el correo leído.
    Ejemplo: INBOX/Procesados_2025-10-15
    """
    # Formar nombre de carpeta con fecha
    #fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    fecha_hoy = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    folder_name = f"{root_folder}/{folder_name}_{fecha_hoy}"

    # Crear carpeta si no existe
    try:
        status, _ = mail.create(folder_name)
        if status == "OK":
            logger.info(f"Carpeta creada: {folder_name}")
        else:
            logger.debug(f"La carpeta {folder_name} ya existe o no se pudo crear.")
    except Exception as e:
        logger.debug(f"No se pudo crear carpeta {folder_name}: {e}")

    # Copiar el mensaje a la carpeta destino
    try:
        status, _ = mail.copy(message_id, folder_name)
        if status == "OK":
            logger.info(f"Correo copiado a {folder_name}")
        else:
            logger.warning(f"No se pudo copiar el correo {message_id} a {folder_name}: {status}")
    except Exception as e:
        logger.error(f"Error al copiar mensaje {message_id} a {folder_name}: {e}")

    # Opcional: eliminar del INBOX original
    mail.store(message_id, '+FLAGS', '\\Deleted')
    mail.expunge()
