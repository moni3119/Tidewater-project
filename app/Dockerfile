FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/settle ./settle
COPY --chown=appuser:appuser tests ./tests

RUN chown -R appuser:appuser /app

USER 10001

EXPOSE 8000

CMD ["uvicorn", "settle.main:app", "--host", "0.0.0.0", "--port", "8000"]