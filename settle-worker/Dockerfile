FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser settle-worker/main.py .

USER 10001

CMD ["python", "-u", "main.py"]