FROM python:3.11-slim

# Ставимо системні бібліотеки для OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Спочатку залежності
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Потім весь код
COPY . /app

# Можна приглушити TF-логи, якщо хочеш
ENV TF_CPP_MIN_LOG_LEVEL=2

# BOT_TOKEN передаєш через Railway → Variables
ENV BOT_TOKEN=""

CMD ["python", "bot.py"]