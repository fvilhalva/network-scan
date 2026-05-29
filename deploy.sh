#!/usr/bin/env bash
set -e

# ── cores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[•]${RESET} $1"; }
success() { echo -e "${GREEN}[✓]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[✗]${RESET} $1"; exit 1; }

echo -e "\n${BOLD}━━━ Network Scanner — Setup ━━━${RESET}\n"

# ── 1. python ──────────────────────────────────────────────────────────────
info "Verificando Python..."
if command -v python3 &>/dev/null; then
    PY=$(python3 --version)
    success "Encontrado: $PY"
else
    error "Python 3 não encontrado. Instale em https://python.org"
fi

# ── 2. venv ────────────────────────────────────────────────────────────────
VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
    warn "venv já existe — pulando criação"
else
    info "Criando ambiente virtual em $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    success "venv criado"
fi

# ── 3. ativa venv ──────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
success "venv ativado"

# ── 4. pip + dependências ──────────────────────────────────────────────────
info "Atualizando pip..."
pip install --upgrade pip -q

info "Instalando dependências de requirements.txt..."
pip install -r requirements.txt -q
success "Dependências instaladas"

# ── 5. cria wrapper de execução ────────────────────────────────────────────
cat > run.sh << 'EOF'
#!/usr/bin/env bash
# Executa o scanner sempre dentro do venv, com sudo se disponível
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$DIR/.venv/bin/python"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "\033[1;33m[!] Rodando sem root — modo ping (sem MAC). Use 'sudo ./run.sh' para modo ARP completo.\033[0m"
fi

"$PY" "$DIR/network_scanner.py" "$@"
EOF
chmod +x run.sh
success "Criado run.sh"

# ── 6. pronto ─────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}━━━ Setup concluído! ━━━${RESET}"
echo -e "  ${BOLD}Rodar agora:${RESET}"
echo -e "    ${CYAN}sudo ./run.sh${RESET}               ← modo completo (ARP + MAC)"
echo -e "    ${CYAN}./run.sh${RESET}                    ← modo ping (sem root)"
echo -e "    ${CYAN}./run.sh 192.168.0.0/24${RESET}    ← range manual\n"
