# Usamos la imagen oficial de Selenium con Chrome preinstalado
FROM selenium/standalone-chrome:latest

# Cambiamos temporalmente a usuario administrador (root) para instalar Python
USER root

# Actualizar el sistema e instalar Python 3 junto con pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos tus archivos del repositorio al contenedor
COPY . .

# Instalamos tus librerías de Python (FastAPI, requests, pydantic, etc.)
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Exponer el puerto estándar requerido por Render
EXPOSE 8080

# Comando para encender el servidor de tu API con FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
