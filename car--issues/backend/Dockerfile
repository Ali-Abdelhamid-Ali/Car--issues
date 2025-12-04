# Backend Dockerfile for Django Car Diagnosis System

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
# Allow choosing a requirements file at build time (default: requirements.txt)
ARG REQUIREMENTS=requirements.txt

# Copy both standard and lightweight requirement files so we can select at build time
COPY requirements.txt requirements.light.txt ./

# Install Python dependencies (selectable via build-arg REQUIREMENTS)
RUN pip install --upgrade pip && \
    pip install -r $REQUIREMENTS

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('wordnet'); nltk.download('stopwords')"

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/ml_models

# Collect static files (will be overridden in docker-compose command)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn car_diagnosis_system.wsgi:application --bind 0.0.0.0:8000 --workers 4"]
