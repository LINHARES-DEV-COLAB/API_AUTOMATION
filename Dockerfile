FROM python:3.12-slim-bookworm

# Chrome + driver (Debian)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver fonts-liberation ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Ambientes
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    XDG_RUNTIME_DIR=/tmp \
    CHROME_TMPDIR=/tmp

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

EXPOSE 10000

# JSON form: um worker/thread (free tier), sem shell
CMD ["gunicorn","--bind","0.0.0.0:10000","--workers","1","--threads","1","--timeout","180","main:create_app()"]
