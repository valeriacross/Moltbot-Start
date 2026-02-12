#!/usr/bin/env bash
set -e

echo "🚀 Build MoltBot..."

# Aggiorna pip PRIMA di apt-get
pip install --upgrade pip setuptools wheel

# Installa dipendenze sistema (senza aggiornare liste)
apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    gcc \
    g++ 2>/dev/null || echo "Alcune dipendenze già installate"

# Installa dipendenze Python
pip install --no-cache-dir -r requirements.txt

echo "✅ Build completato!"
