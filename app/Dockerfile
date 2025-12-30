# build with `docker build -t impossible-travel-api .`
# run with `docker run -p 80:80 -v $(pwd)/data:/opt/copilot/app/data -d impossible-travel-api`
# Start with Python 3.11 on Debian 12 (bookworm) slim
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /opt/copilot/app

# Install system dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite database
RUN mkdir -p /opt/copilot/app/data

# Expose port
EXPOSE 80

# Run the application
CMD ["python", "module.py"]
