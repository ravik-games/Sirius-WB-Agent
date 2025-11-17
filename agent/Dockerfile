FROM python:3.11-slim

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt
RUN playwright install-deps
RUN playwright install chromium

RUN playwright install-deps
RUN playwright install chromium

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8037"]
