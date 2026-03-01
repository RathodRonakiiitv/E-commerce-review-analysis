FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (gcc for C extensions, plus Playwright OS deps)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser + its OS-level dependencies
RUN playwright install --with-deps chromium

# Copy application
COPY . .

# Set environment variable for UTF-8 encoding
ENV PYTHONIOENCODING=utf-8

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
