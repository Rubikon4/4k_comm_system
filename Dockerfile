FROM python:3.12-slim

# libmagic1 нужен для python-magic (определение MIME-типа файлов на runtime)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаём непривилегированного пользователя, чтобы процесс не шёл от root
RUN addgroup --system web && adduser --system --ingroup web web

# Зависимости ставим отдельным слоем — кэшируется при неизменном requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Директории для медиафайлов и собранной статики — заранее, с нужным владельцем
RUN mkdir -p /app/media /app/staticfiles && chown -R web:web /app

USER web

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
