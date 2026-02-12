#!/usr/bin/env bash
# render-build.sh - Script di build per Render.com

set -e  # Exit on error

echo "🚀 Inizio build MoltBot 4K..."

# Aggiorna lista pacchetti
echo "📦 Aggiornamento apt..."
apt-get update -qq

# Installa dipendenze di sistema per Pillow
echo "🔧 Installazione dipendenze sistema..."
apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    gcc \
    g++

# Pulisci cache apt
apt-get clean
rm -rf /var/lib/apt/lists/*

# Aggiorna pip
echo "⬆️ Aggiornamento pip..."
pip install --upgrade pip setuptools wheel

# Installa dipendenze Python
echo "🐍 Installazione dipendenze Python..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build completato con successo!"
