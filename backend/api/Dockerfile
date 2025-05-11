FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY ./backend/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./backend/api /app

# Port that Cloud Run expects
ENV PORT 8080

# Command to run when container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
