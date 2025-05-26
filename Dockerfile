# Use an official Python runtime
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install spaCy and English model
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy the application files
COPY . .

# Expose Flask port
EXPOSE 5000

# Run the application
CMD ["python", "agent_server.py"]
