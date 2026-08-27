# Usamos una imagen oficial y ligera de Python
FROM python:3.10-slim

# Definimos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el archivo de dependencias para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos las librerías necesarias sin caché para ahorrar espacio
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de los archivos del proyecto (script, CSVs, etc.) al contenedor
COPY . .

# Comando que se ejecutará por defecto al arrancar el contenedor
CMD ["python", "tecnologia.py"]