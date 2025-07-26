FROM python:3.12-slim

WORKDIR /app

# Sistem kutubxonalarni yangilaymiz va ffmpeg o‘rnatamiz
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python optimallashtirishlar
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Pip yangilanishi
RUN pip install --upgrade pip

# Kerakli Python kutubxonalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyihani nusxalash
COPY . .

# Django uchun port
EXPOSE 8000

# Botni ishga tushirish
CMD ["sh", "-c", "python3 manage.py bot"]