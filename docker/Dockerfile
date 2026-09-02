FROM python:3.11-slim

WORKDIR /app

# Install system utilities and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy application source code
COPY backend /app/backend
COPY frontend /app/frontend
COPY data /app/data
COPY seed_data.py /app/seed_data.py

# Create directory structure
RUN mkdir -p /app/data/uploads /app/data/chroma_db /app/data/sample_docs

EXPOSE 8000

# Run seed data script and start Uvicorn server
CMD python seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
