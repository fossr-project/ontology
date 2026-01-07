# Dockerfile.builder - Survey Builder Flask Application

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*



# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL Python files
COPY *.py .

# Copy LOCAL pyrml ✅
COPY pyrml/ ./pyrml/

# Copy static files
COPY static/ ./static/

# Copy templates
COPY templates/ ./templates/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5005/ || exit 1

# Run the application
CMD ["python", "app.py"]