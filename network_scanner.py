#!/usr/bin/env python3
"""
network_scanner.py — Escaneador de dispositivos na rede local
Requer: pip install scapy mac-vendor-lookup rich

Uso:
  python network_scanner.py               # detecta a rede automaticamente
  python network_scanner.py 192.168.1.0/24  # especifica o range manualmente
"""

import sys
import socket
import subprocess
import concurrent.futures
from datetime import datetime

# ── dependências opcionais ──────────────────────────────────────────────────
try:
    from scapy.all import ARP, Ether, srp
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

try:
    from mac_vendor_lookup import MacLookup
    HAS_MAC_VENDOR = True
except ImportError:
    HAS_MAC_VENDOR = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ── utilitários ────────────────────────────────────────────────────────────

def get_hostname(ip: str, timeout: float = 1.0) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "—"


def get_mac_vendor(mac: str) -> str:
    if not HAS_MAC_VENDOR:
        return "—"
    try:
        return MacLookup().lookup(mac)
    except Exception:
        return "—"


def ping(ip: str, timeout: int = 1) -> bool:
    """Ping rápido sem precisar de root (fallback quando scapy não está disponível)."""
    param = "-n" if sys.platform == "win32" else "-c"
    cmd = ["ping", param, "1", "-W", str(timeout), ip]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=timeout + 1)
        return result.returncode == 0
    except Exception:
        return False


def detect_local_network() -> str:
    """Detecta o range da rede local automaticamente."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return "192.168.1.0/24"


# ── escaneamento com Scapy (ARP — mais preciso, precisa de root) ───────────

def scan_with_scapy(network: str) -> list[dict]:
    """Usa ARP broadcast — retorna MAC real + IP de todos os dispositivos ativos."""
    arp = ARP(pdst=network)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    answered, _ = srp(packet, timeout=3, verbose=False)

    devices = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        futures = {}
        for sent, received in answered:
            ip = received.psrc
            mac = received.hwsrc
            futures[pool.submit(get_hostname, ip)] = (ip, mac)

        for future, (ip, mac) in futures.items():
            hostname = future.result()
            vendor = get_mac_vendor(mac)
            devices.append({
                "ip": ip,
                "mac": mac,
                "hostname": hostname,
                "vendor": vendor,
            })

    devices.sort(key=lambda d: list(map(int, d["ip"].split("."))))
    return devices


# ── escaneamento com ping (sem root, mais lento) ───────────────────────────

def scan_with_ping(network: str) -> list[dict]:
    """Faz ping em cada IP do /24 — não retorna MAC, mas funciona sem root."""
    # extrai o prefixo: 192.168.1.0/24 → 192.168.1.
    base = ".".join(network.split("/")[0].split(".")[:3]) + "."
    ips = [f"{base}{i}" for i in range(1, 255)]

    alive = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as pool:
        results = {pool.submit(ping, ip): ip for ip in ips}
        for future in concurrent.futures.as_completed(results):
            ip = results[future]
            if future.result():
                alive.append(ip)

    devices = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
        hostname_futures = {pool.submit(get_hostname, ip): ip for ip in alive}
        for future in concurrent.futures.as_completed(hostname_futures):
            ip = hostname_futures[future]
            devices.append({
                "ip": ip,
                "mac": "N/A (sem root)",
                "hostname": future.result(),
                "vendor": "—",
            })

    devices.sort(key=lambda d: list(map(int, d["ip"].split("."))))
    return devices


# ── saída ──────────────────────────────────────────────────────────────────

def print_rich(devices: list[dict], network: str, method: str, elapsed: float):
    console = Console()
    console.print()
    console.print(f"[bold cyan]🔍 Network Scanner[/bold cyan]  |  rede: [yellow]{network}[/yellow]  |  método: [green]{method}[/green]")
    console.print(f"[dim]Escaneado em {elapsed:.1f}s  ·  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/dim]")
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("IP", style="cyan", min_width=15)
    table.add_column("MAC", style="yellow", min_width=18)
    table.add_column("Hostname", style="green", min_width=20)
    table.add_column("Fabricante (MAC)", style="white", min_width=20)

    for i, d in enumerate(devices, 1):
        table.add_row(str(i), d["ip"], d["mac"], d["hostname"], d["vendor"])

    console.print(table)
    console.print(f"\n[bold]Total: {len(devices)} dispositivo(s) encontrado(s)[/bold]\n")


def print_plain(devices: list[dict], network: str, method: str, elapsed: float):
    print(f"\n=== Network Scanner | rede: {network} | método: {method} ===")
    print(f"Escaneado em {elapsed:.1f}s  ·  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    header = f"{'#':<4} {'IP':<16} {'MAC':<20} {'Hostname':<30} {'Fabricante'}"
    print(header)
    print("-" * len(header))
    for i, d in enumerate(devices, 1):
        print(f"{i:<4} {d['ip']:<16} {d['mac']:<20} {d['hostname']:<30} {d['vendor']}")
    print(f"\nTotal: {len(devices)} dispositivo(s)\n")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    network = sys.argv[1] if len(sys.argv) > 1 else detect_local_network()

    if HAS_RICH:
        console = Console()
        with Progress(SpinnerColumn(), TextColumn("[cyan]Escaneando {task.description}..."),
                      console=console, transient=True) as progress:
            task = progress.add_task(network)
            t0 = datetime.now()
            if HAS_SCAPY:
                method = "ARP/Scapy (preciso)"
                devices = scan_with_scapy(network)
            else:
                method = "Ping (sem root)"
                devices = scan_with_ping(network)
            elapsed = (datetime.now() - t0).total_seconds()
        print_rich(devices, network, method, elapsed)
    else:
        print(f"Escaneando {network}...")
        t0 = datetime.now()
        if HAS_SCAPY:
            method = "ARP/Scapy"
            devices = scan_with_scapy(network)
        else:
            method = "Ping"
            devices = scan_with_ping(network)
        elapsed = (datetime.now() - t0).total_seconds()
        print_plain(devices, network, method, elapsed)


if __name__ == "__main__":
    main()
