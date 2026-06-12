#!/usr/bin/env bash
#
# PHPBox installer (Linux / macOS)
#
# Installs the latest PHPBox straight from GitHub — no clone required. Run it
# directly or pipe it in:
#
#   curl -fsSL https://raw.githubusercontent.com/manishkumar1601/phpbox/master/scripts/install.sh | bash
#
# Missing prerequisites are installed automatically where possible:
#   * Python 3.12+  (required to run the PHPBox CLI)
#   * Docker        (required only when you `phpbox start` a project)
#
# Flags (when run as a file): --pip (use pip), --skip-deps (don't install Python/Docker)
#
set -euo pipefail

# Latest PHPBox, as a GitHub source tarball (no git / clone needed).
SPEC="https://github.com/manishkumar1601/phpbox/archive/refs/heads/master.tar.gz"
USE_PIP=0
SKIP_DEPS=0
for arg in "$@"; do
  case "$arg" in
    --pip) USE_PIP=1 ;;
    --skip-deps) SKIP_DEPS=1 ;;
  esac
done

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[1;33m%s\033[0m\n' "$1"; }
red() { printf '\033[1;31m%s\033[0m\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"

# Return the name of a Python >= 3.12 on PATH (echo it), or nothing.
find_python() {
  for c in python3 python; do
    if have "$c" && "$c" -c 'import sys;exit(0 if sys.version_info[:2]>=(3,12) else 1)' 2>/dev/null; then
      echo "$c"; return 0
    fi
  done
  return 1
}

install_python() {
  if [ "$OS" = "Darwin" ]; then
    if have brew; then
      bold "Installing Python via Homebrew..."; brew install python@3.12 || true
    else
      red "Homebrew not found. Install Python 3.12+ from https://www.python.org/downloads/ (or 'brew install python@3.12')."
      return 1
    fi
  else
    if have apt-get; then
      bold "Installing Python via apt..."; sudo apt-get update -y && sudo apt-get install -y python3 python3-pip python3-venv
    elif have dnf; then
      bold "Installing Python via dnf..."; sudo dnf install -y python3 python3-pip
    elif have pacman; then
      bold "Installing Python via pacman..."; sudo pacman -Sy --noconfirm python python-pip
    elif have zypper; then
      bold "Installing Python via zypper..."; sudo zypper install -y python3 python3-pip
    else
      red "No supported package manager found. Install Python 3.12+ manually."
      return 1
    fi
  fi
}

install_docker() {
  if [ "$OS" = "Darwin" ]; then
    if have brew; then
      bold "Installing Docker Desktop via Homebrew..."; brew install --cask docker || true
      yellow "Docker Desktop installed. Launch Docker from Applications once before 'phpbox start'."
    else
      yellow "Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    fi
  else
    yellow "Installing Docker Engine via the official script (needs sudo)..."
    if have curl; then
      curl -fsSL https://get.docker.com | sudo sh && \
        sudo usermod -aG docker "$USER" 2>/dev/null || true
      yellow "If 'docker' needs sudo, log out/in so the 'docker' group applies."
    else
      yellow "Install Docker: https://docs.docker.com/engine/install/"
    fi
  fi
}

bold "Installing the latest PHPBox from GitHub..."

# === 1. Ensure Python ====================================================
PY="$(find_python || true)"
if [ -z "$PY" ]; then
  if [ "$SKIP_DEPS" -eq 1 ]; then
    red "Python 3.12+ not found and --skip-deps was given. Install it and re-run."
    exit 1
  fi
  install_python || true
  PY="$(find_python || true)"
fi
if [ -z "$PY" ]; then
  red "Python 3.12+ is still not available. Install it, then re-run this script."
  exit 1
fi
echo "Using $PY ($("$PY" -c 'import sys;print("%d.%d"%sys.version_info[:2])'))"

# === 2. Install PHPBox ===================================================
if [ "$USE_PIP" -eq 1 ]; then
  bold "Installing PHPBox with pip (--user)..."
  "$PY" -m pip install --user --upgrade "$SPEC"
  HINT="Make sure your Python user scripts directory is on your PATH."
else
  if ! "$PY" -m pipx --version >/dev/null 2>&1; then
    bold "Installing pipx..."
    "$PY" -m pip install --user pipx
    "$PY" -m pipx ensurepath
  fi
  bold "Installing PHPBox with pipx..."
  "$PY" -m pipx install --force "$SPEC"
  HINT="pipx put 'phpbox' on your PATH."
fi

# === 3. Ensure Docker (runtime only) =====================================
DOCKER_NOTE=""
if have docker; then
  if docker info >/dev/null 2>&1; then
    green "Docker is installed and running."
  else
    DOCKER_NOTE="Docker is installed but not running - start it before 'phpbox start'."
  fi
elif [ "$SKIP_DEPS" -eq 1 ]; then
  DOCKER_NOTE="Docker not found. Install it before running projects: https://docs.docker.com/get-docker/"
else
  install_docker || true
  have docker || DOCKER_NOTE="Docker is required to run projects: https://docs.docker.com/get-docker/"
fi

# === Done ================================================================
echo
green "✓ PHPBox installed."
echo "$HINT"
[ -n "$DOCKER_NOTE" ] && yellow "$DOCKER_NOTE"
echo "Open a NEW terminal, then run:  phpbox --help"
