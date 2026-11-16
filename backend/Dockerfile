FROM python:3.12-slim

WORKDIR /app

# Trivy is a standalone binary the backend shells out to for image scanning.
# Without it, POST /api/scan/image returns a 503 inside the container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin \
    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]