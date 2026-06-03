# Usamos una imagen de Linux que ya viene con Python, Chrome y sus drivers preinstalados
FROM joyzourschaefer/python-selenium:latest

WORKDIR /app

# Copiamos tus archivos del repositorio al servidor
COPY . .

# Instalamos las librerías de Python (FastAPI, Selenium, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Abrimos el puerto estándar para Render
EXPOSE 8080

# Comando para encender tu servidor API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
