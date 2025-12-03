FROM python:3.11-slim

WORKDIR /app

# копіюємо всі файли проекту
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]