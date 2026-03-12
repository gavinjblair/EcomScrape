FROM python:3.11-slim

WORKDIR /app

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Railway provides PORT; default to 8080 if not set
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn ecomscrape.api:app --host 0.0.0.0 --port ${PORT}"]
