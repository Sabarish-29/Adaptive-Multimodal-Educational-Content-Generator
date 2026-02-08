# NeuroSync AI – Base Node.js image for web frontend

FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Default command
CMD ["npm", "run", "dev"]
