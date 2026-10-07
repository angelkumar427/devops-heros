# python:3.12-slim chosen deliberately: a local Trivy scan showed 0 fixable
# HIGH/CRITICAL findings, versus 7 for python:3.12-alpine.
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} PORT=8080 PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app.server:app"]
