# Base Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# portaudio19-dev is required for PyAudio
# build-essential is for gcc compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
