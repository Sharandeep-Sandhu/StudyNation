FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV DEBUG=False

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -q -r requirements.txt

# Copy project
COPY . .

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles

# Entrypoint runs migrate + collectstatic at container start (needs live DB)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Render sets PORT at runtime; document default for local runs
EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
# Default: gunicorn on $PORT (see docker-entrypoint.sh). Override CMD if needed.
CMD []
