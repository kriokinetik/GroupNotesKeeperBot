FROM python:3.11-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/bot

ENTRYPOINT [ "python", "./main.py" ]
