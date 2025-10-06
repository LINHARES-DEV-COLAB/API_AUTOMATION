FROM python:3.12-slim

# 1) Dependências do Chrome e utilitários
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver fonts-liberation ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2) Variáveis exigidas pelo código
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# 3) App
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

# 4) Expose + CMD
EXPOSE 10000
# Gunicorn lê PORT do ambiente da Render. Bind em 0.0.0.0
CMD exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 1 --timeout 180 "main:create_app()"

 

