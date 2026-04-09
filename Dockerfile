# ── Stage 1: Build Vue.js frontend ──────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# Install dependencies (cached layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

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
    libgdk-pixbuf2.0-0 \
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

# Copy built Vue.js frontend from stage 1
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Ensure data directory exists and is owned by solde user
RUN mkdir -p /app/data/pdfs /app/data/uploads \
    && chown -R solde:solde /app/data

USER solde

EXPOSE 8000

# Run Alembic migrations then start Uvicorn
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1"]
