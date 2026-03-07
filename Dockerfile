FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/

# Expose port (Render sets PORT dynamically)
EXPOSE 10000

# Run migrations then start the application
CMD sh -c "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-10000}"
