FROM python:3.10-slim

WORKDIR /app

# Nastavení ENV proměnných pro zamezení generování .pyc souborů a pro přímý výstup
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Zkopírování a instalace závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Zkopírování celé aplikace
COPY . .

EXPOSE 8000

# Spuštění migrací a následně web serveru
# --reload je skvělý pro vývoj.
# Pro produkci by se příkaz změnil na:
# CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]