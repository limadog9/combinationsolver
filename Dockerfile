# Use official Python image as base
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy application files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on (Google Cloud Run uses 8080)
EXPOSE 8080

# Set Gunicorn timeout to prevent Cloud Run from killing it too soon
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "120", "app:app"]
