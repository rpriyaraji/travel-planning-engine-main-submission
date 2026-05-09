# =============================================================================
# Stage 1: Build the React frontend
# =============================================================================
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy dependency manifests first for better layer caching.
# package-lock.json is copied with a wildcard so the build doesn't fail when
# it doesn't exist (create-react-app projects may omit it).
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies. Falls back to `npm install` when no lockfile is present.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source and public assets, then produce an optimised production build.
COPY frontend/src ./src
COPY frontend/public ./public

ARG REACT_APP_MAPS_API_KEY=""
ENV REACT_APP_MAPS_API_KEY=$REACT_APP_MAPS_API_KEY

RUN npm run build

# =============================================================================
# Stage 2: Python / FastAPI backend — serves the API and the built frontend
# =============================================================================
FROM python:3.11-slim

# Create a non-root user that will own and run the application.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

WORKDIR /app

# Install Python dependencies before copying source so this layer is cached
# as long as requirements.txt doesn't change.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    # starlette (bundled with FastAPI) provides StaticFiles; install explicitly
    # in case a minimal requirements.txt omits it.
    pip install --no-cache-dir starlette

# Copy backend source code.
COPY backend/ ./backend/

# Copy the compiled React build from Stage 1.
# FastAPI mounts this directory via StaticFiles in backend/main.py so that the
# frontend is served at the root path alongside the /api routes.
COPY --from=frontend-build /app/frontend/build ./frontend/build/

# Transfer ownership to the non-root user.
RUN chown -R appuser:appgroup /app

# Switch to non-root user for runtime.
USER appuser

# Cloud Run injects PORT at runtime; default to 8080 for local runs.
ENV PORT=8080

# Start the ASGI server. The module path matches the backend package layout:
#   /app/backend/main.py  →  backend.main:app
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
