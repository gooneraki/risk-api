FROM python:3.11.9-slim

WORKDIR /app

# Copy and install requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add curl for healthcheck
RUN apt-get update && apt-get install -y curl && apt-get clean

# Copy only the application code
COPY app/ ./app/

EXPOSE 10000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]