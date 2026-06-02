FROM python:3.10-slim

RUN apt-get update && apt-get install -y wget gnupg unzip curl \
    && curl -sSL https://google.com | apt-key add - \
    && echo "deb [arch=amd64] http://google.com stable main" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
