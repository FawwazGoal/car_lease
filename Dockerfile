# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/browsers

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create output directory
RUN mkdir -p /app/data

# Create volume for data persistence
VOLUME ["/app/data"]

# Set the entrypoint
ENTRYPOINT ["python", "-m", "car_lease_scraper"]

# Default command (can be overridden)
CMD ["--provider", "anwb", "--output-format", "json,csv", "--output-dir", "/app/data"]