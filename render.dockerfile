FROM python:3.10-slim

# Installer FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Exposer le port (Render le définit via PORT)
ENV PORT=10000

# Lancer Gunicorn
CMD ["gunicorn", "app:app"]
