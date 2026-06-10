#!/usr/bin/env bash
#
# PHPBox uninstaller (Linux / macOS)
#
# Removes the `phpbox` command, whether it was installed via pipx or pip.
#
set -uo pipefail

green() { printf '\033[1;32m%s\033[0m\n' "$1"; }

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then PY="python3"; fi

removed=0

# Try pipx first.
if "$PY" -m pipx list 2>/dev/null | grep -qi 'package phpbox'; then
  echo "Removing pipx install…"
  "$PY" -m pipx uninstall phpbox && removed=1
fi

# Fall back to pip.
if [ "$removed" -eq 0 ]; then
  echo "Removing pip install…"
  "$PY" -m pip uninstall -y phpbox || true
fi

green "✓ PHPBox uninstalled."
echo "Your projects and their .phpbox/ folders are untouched."
echo "Remove a project's containers with: docker compose -f <project>/.phpbox/docker-compose.yml down -v"
