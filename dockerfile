FROM python:3.11-slim

# Install system dependencies for Pygame and PyInstaller
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libfreetype6-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libjpeg-dev \
    libtiff-dev \
    libx11-dev \
    libpng-dev \
    git curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install pygame pyinstaller pathfinding perlin-noise

# Set working directory
WORKDIR /app

# Copy your game files into the container
COPY . .

# Build with pyinstaller
RUN pyinstaller -y --onefile --windowed main.py \
  --add-data="textures:textures" \
  --add-data="audio:audio" \
  --add-data="data:data" \
  --add-data="saves:saves" \
  --add-data="Pixellari.ttf:." \
  --icon=icon.ico

# Final output will be in /app/dist
