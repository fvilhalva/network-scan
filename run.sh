#!/usr/bin/env bash
# Executa o scanner sempre dentro do venv, com sudo se disponível
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$DIR/.venv/bin/python"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "\033[1;33m[!] Rodando sem root — modo ping (sem MAC). Use 'sudo ./run.sh' para modo ARP completo.\033[0m"
fi

"$PY" "$DIR/network_scanner.py" "$@"
