FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

# Expose HTTP bridge port (for Make.com webhooks)
EXPOSE 8000

# Default: run the MCP server in HTTP bridge mode via uvicorn
CMD ["uvicorn", "webhooks.http_bridge:app", "--host", "0.0.0.0", "--port", "8000"]
