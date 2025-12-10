# Usar una imagen base de Python ligera
FROM python:3.10-slim

# Instalar 'unzip' por si el módulo zipfile de python lo necesita (aunque no suele)
RUN apt-get update && apt-get install -y unzip && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requisitos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de la aplicación
COPY app.py .

# Comando para ejecutar la aplicación cuando el contenedor inicie
# Gunicorn es más robusto que 'flask run' pero para esto 'python app.py' vale.
CMD ["python", "app.py"]
