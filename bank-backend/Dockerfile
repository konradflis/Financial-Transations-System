# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY bank-backend/requirements.txt .

ENV PYTHONPATH=/app/src

RUN pip install --no-cache-dir -r requirements.txt

COPY bank-backend .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]