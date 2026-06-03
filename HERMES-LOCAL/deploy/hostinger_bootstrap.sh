#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/hermes-filadelfia"
REPO_URL="${REPO_URL:-https://github.com/haniellevi/gestor-pastoral-agente-hermes.git}"
BRANCH="${BRANCH:-feature/instalacao-hermes}"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl git ufw

if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

mkdir -p "$PROJECT_DIR"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
else
  git -C "$PROJECT_DIR" fetch origin "$BRANCH"
  git -C "$PROJECT_DIR" checkout "$BRANCH"
  git -C "$PROJECT_DIR" pull --ff-only origin "$BRANCH"
fi

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "Arquivo .env criado em $PROJECT_DIR/.env"
  echo "Edite esse arquivo com SUPABASE_SERVICE_ROLE_KEY e BOTCONVERSA_API_KEY antes de subir os containers."
  exit 0
fi

mkdir -p database config
docker compose up -d --build

ufw allow OpenSSH || true
ufw allow 5050/tcp || true
ufw allow 8501/tcp || true
ufw --force enable || true

docker compose ps

