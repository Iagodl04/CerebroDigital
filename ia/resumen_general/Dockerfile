FROM python:3.9-slim

    WORKDIR /app

    # Instal·lem dependències
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copiem tot el codi
    COPY . .

    # Exposem el port
    EXPOSE 8000

    # Arrenquem l'API
    CMD ["uvicorn", "IAapi:app", "--host", "0.0.0.0", "--port", "8000"]
