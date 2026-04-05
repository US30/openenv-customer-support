FROM python:3.11-slim

WORKDIR /app

# Install dependencies including openenv-core
RUN pip install --no-cache-dir fastapi uvicorn pydantic openenv-core

# Copy the app files
COPY . .

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
