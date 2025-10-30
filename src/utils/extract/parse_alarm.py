'''
Created on 4 ago 2025

@author: jlcartas
'''
import re
from utils.logger import LoggerSingleton

logger = LoggerSingleton.get_logger("utils.extract.parse_alarm")
NOT_AVAILABLE = "Not available"

def parse_alarm(texto: str, patterns) -> dict:
    texto = re.sub(r'\s+', ' ', texto.strip())  # Normalizar

    # Buscar el patrón adecuado
    patrones = list(patterns)
    patron_usado = None
    for patron in patrones:
        if patron["pattern_deteccion"] in texto:
            patron_usado = patron
            break

    if not patron_usado:
        raise ValueError("No se encontró un patrón compatible para el texto.")
    
    resultado = {
            "tipo_alarma": NOT_AVAILABLE,
            "tiempo_alarma": NOT_AVAILABLE,
            "fuente_alarma": NOT_AVAILABLE,
            "nombre_dispositivo": NOT_AVAILABLE,
            "no_dispositivo": "1",
            "num_serie": NOT_AVAILABLE,
            "ip_dispositivo": NOT_AVAILABLE,
            "tipo_eventos": NOT_AVAILABLE,
            "canal": "0"
    }

    # Aplicar expresiones regulares desde Mongo
    for campo, patron_regex in patron_usado["regex_campos"].items():
        match = re.search(patron_regex, texto)
        if match:
            resultado[campo] = match.group(1).strip()

    return resultado