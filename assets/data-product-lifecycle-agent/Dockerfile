FROM python:3.13-slim

# Non-root user for security
RUN groupadd -r agent && useradd -r -g agent agent

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent source code
COPY app/ ./

# Switch to non-root user
USER agent

EXPOSE 5000

CMD ["python", "main.py"]
