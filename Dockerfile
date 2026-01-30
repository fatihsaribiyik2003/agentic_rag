# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Environment variable for unbuffered logs
ENV PYTHONUNBUFFERED=1

# Run server.py using uvicorn. 
# IMPORTANT: Cloud Run injects the PORT environment variable. We must listen on 0.0.0.0.
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]


