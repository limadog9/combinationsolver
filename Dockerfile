# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy all files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask’s port
EXPOSE 8080

# Run Flask using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
