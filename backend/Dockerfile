# Use a stable, lightweight Python slim image
FROM python:3.10-slim

# Set environment variables for performance and logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies, optimizing PyTorch for CPU-only to minimize image size (saves ~2GB)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the backend files (excluding best_model if ignored via .dockerignore)
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the FastAPI server using Uvicorn
CMD ["python", "app.py"]
