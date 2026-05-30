# 🔍 Network Scanner

Escaneador de dispositivos na rede local, escrito em Python. Detecta automaticamente todos os hosts ativos na sua rede e exibe **IP**, **MAC**, **hostname** e **fabricante** em uma tabela colorida no terminal.

## ✨ Funcionalidades

- Detecção automática do range da rede local (`/24`)
- Dois modos de varredura:
  - **ARP/Scapy** (preciso, retorna MAC real) — requer root/sudo
  - **Ping** (fallback sem privilégios) — funciona sem root
- Resolução de hostname via DNS reverso
- Identificação do fabricante a partir do OUI do MAC
- Saída formatada com [`rich`](https://github.com/Textualize/rich) (tabelas, cores, spinner)
- Escaneamento concorrente com `ThreadPoolExecutor`

## 📦 Requisitos

- Python 3.8+
- Linux/macOS (o `run.sh` é shell script; no Windows, rode `python network_scanner.py` direto)

Dependências (em `requirements.txt`):

```
scapy>=2.5.0
mac-vendor-lookup>=0.1.12
rich>=13.0.0
```

## 🚀 Instalação

```bash
git clone <repo-url>
cd network-scan
chmod +x deploy.sh
./deploy.sh
```

O `deploy.sh` faz:

1. Verifica Python 3
2. Cria um virtualenv em `.venv/`
3. Instala as dependências
4. Gera o wrapper `run.sh`

## 🖥️ Uso

```bash
sudo ./run.sh                    # modo completo (ARP + MAC)
./run.sh                         # modo ping (sem root, sem MAC)
./run.sh 192.168.0.0/24          # range manual
```

Ou diretamente:

```bash
sudo python network_scanner.py
python network_scanner.py 10.0.0.0/24
```

## 📋 Exemplo de saída

```
🔍 Network Scanner  |  rede: 192.168.1.0/24  |  método: ARP/Scapy (preciso)
Escaneado em 3.2s  ·  29/05/2026 14:32:10

╭────┬─────────────────┬───────────────────┬──────────────────────┬──────────────────────╮
│  # │ IP              │ MAC               │ Hostname             │ Fabricante (MAC)     │
├────┼─────────────────┼───────────────────┼──────────────────────┼──────────────────────┤
│  1 │ 192.168.1.1     │ aa:bb:cc:dd:ee:ff │ router.local         │ TP-Link              │
│  2 │ 192.168.1.10    │ 11:22:33:44:55:66 │ felipe-pc            │ Intel Corporate      │
╰────┴─────────────────┴───────────────────┴──────────────────────┴──────────────────────╯

Total: 2 dispositivo(s) encontrado(s)
```

## 📁 Estrutura

```
network-scan/
├── network_scanner.py   # script principal
├── requirements.txt     # dependências Python
├── deploy.sh            # setup automático (venv + deps)
├── run.sh               # wrapper de execução (gerado pelo deploy)
├── run.bat              # wrapper para Windows
└── .gitignore
```

## ⚠️ Observações

- Sem `sudo`, o Scapy não consegue enviar pacotes ARP — o script cai automaticamente no modo ping (sem MAC).
- A varredura ARP só funciona dentro da própria subnet (broadcast L2).
- Alguns dispositivos podem não responder a ping mesmo estando ativos (firewall).

## 📄 Licença

Uso livre para fins educacionais.
