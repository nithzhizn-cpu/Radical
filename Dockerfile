# ===========================
#  BASE IMAGE
# ===========================
FROM python:3.11-slim

# ===========================
#  FIX OpenCV (libGL.so.1 error)
# ===========================
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# ===========================
#  Create work directory
# ===========================
WORKDIR /app

# ===========================
#  Install Python dependencies
# ===========================
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ===========================
#  Copy bot files
# ===========================
COPY . /app/

# ===========================
#  Run the bot
# ===========================
CMD ["python", "bot.py"]