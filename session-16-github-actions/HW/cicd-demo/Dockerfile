FROM python:3.12-slim

# Run as a non-root user
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} PORT=8080
USER appuser
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app.server:app"]
