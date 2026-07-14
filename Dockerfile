FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn httpx

# Copy app
COPY . .

# Build index & validate
RUN python scripts/build_index.py && python scripts/validate.py

EXPOSE 8000

# Use uvicorn directly for reliability
CMD uvicorn api_server.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
# Build 20260714-v2
