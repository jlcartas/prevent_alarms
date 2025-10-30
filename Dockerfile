# Imagen base ligera de Python
FROM python:3.11-slim

# Evita archivos .pyc y usa salida directa en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crea el directorio de trabajo
WORKDIR /app

# Copia las dependencias
COPY requirements.txt .

# Instala dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY src/ .

# Expone el puerto de tu backend (ajústalo si usas otro)
EXPOSE 8000

# Para depurar, instalamos ptvsd (para Eclipse, VSCode, etc.)
RUN pip install debugpy

# Comando por defecto al iniciar el contenedor
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "main.py"]