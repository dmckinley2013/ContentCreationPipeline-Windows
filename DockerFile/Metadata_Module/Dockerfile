# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port if your app needs to listen on one (optional)
EXPOSE 5000

# Command to run your Python module (replace with your actual entry point)
CMD ["python", "metabackendwindows.py"]
