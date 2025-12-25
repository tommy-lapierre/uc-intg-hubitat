# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy integration files
COPY intg-hubitat/ ./intg-hubitat/

# Create config directory
RUN mkdir -p /app/config

# Expose the WebSocket port
EXPOSE 9087

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV UC_CONFIG_HOME=/app/config

# Run the integration
CMD ["python", "intg-hubitat/driver.py"]
