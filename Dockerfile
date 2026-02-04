FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 5000

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120"]
