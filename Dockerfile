# ── Stage 1: Build Vue.js frontend ──────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# Install dependencies (cached layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy pyproject.toml so vite.config.ts can read the version
COPY pyproject.toml ../

# Copy source and build
COPY frontend/ ./
RUN npm run build-only


# ── Stage 2: Python runtime ──────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# WeasyPrint requires Pango + Cairo + GDK-Pixbuf for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN addgroup --system solde && adduser --system --ingroup solde solde

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy backend source
COPY backend/ ./backend/
COPY alembic.ini ./
COPY doc/ ./doc/


# Copy built Vue.js frontend from stage 1
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist
# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure data directory exists and is owned by solde user
RUN mkdir -p /app/data/pdfs /app/data/uploads \
    && chown -R solde:solde /app/data

# Copy entrypoint script
COPY entrypoint.sh ./
USER solde

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["sh", "entrypoint.sh"]
