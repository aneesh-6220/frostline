# Frostline web app: React frontend (UI/frontend) built with Node, served with the analysis API (UI/api) by Python.
# Works on Render, Railway, Fly.io and Hugging Face Spaces (Docker SDK). The app listens on $PORT (default 7860).
FROM node:22-slim AS web
WORKDIR /web
COPY UI/frontend/package.json UI/frontend/package-lock.json ./
RUN npm ci
COPY UI/frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY UI/requirements.txt UI/requirements.txt
COPY UI/api/requirements.txt UI/api/requirements.txt
RUN pip install --no-cache-dir -r UI/api/requirements.txt
COPY . .
COPY --from=web /web/dist UI/frontend/dist
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn UI.api.server:app --host 0.0.0.0 --port ${PORT}"]
