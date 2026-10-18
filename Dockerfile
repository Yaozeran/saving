FROM node:24-bookworm-slim AS webbuild
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV NODE_ENV=production APP_ENV=production PORT=10000 HOSTNAME=0.0.0.0 API_PORT=4000 DB_PATH=/app/data/saving.sqlite PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
# Node is only for the Next.js frontend and process supervisor.
COPY --from=webbuild /usr/local/bin/node /usr/local/bin/node
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/main.py backend/config.py backend/database.py backend/security.py backend/chain.py backend/rpc_errors.py ./
WORKDIR /app/web
COPY --from=webbuild /app/web/.next/standalone ./
COPY --from=webbuild /app/web/.next/static ./.next/static
COPY --from=webbuild /app/web/public ./public
COPY start.mjs /app/start.mjs
RUN useradd --create-home --uid 1000 appuser && mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 10000
CMD ["node", "/app/start.mjs"]
