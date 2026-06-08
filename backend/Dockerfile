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

# Use lightweight sentiment on Render (free tier has limited RAM)
ENV LIGHTWEIGHT_SENTIMENT=true

# Use HTTP-based scraper on Render (Playwright is too heavy and cloud IPs
# are blocked by Flipkart's anti-bot systems)
ENV LIGHTWEIGHT_SCRAPER=true

# Download NLTK VADER lexicon for lightweight sentiment
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/share/nltk_data')"

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
