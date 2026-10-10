import sys
import time
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from sector_engine import SectorFlowEngine
from anomalies import SectorAnomalyDetector

console = Console()

def render_screen(sector_results, signals, timeframe="1h"):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Header Panel
    header_text = Text()
    header_text.append("🔥 KRİPTO SEKTÖREL NET PARA AKIMI RADARI (BINANCE FUTURES CVD) 🔥\n", style="bold cyan")
    header_text.append(f"Zaman Penceresi: [{timeframe}] | Son Güncelleme: {now_str} | Motor: Taker Volume Delta", style="dim white")
    console.print(Panel(header_text, style="cyan", border_style="bright_blue"))

    # Main Sector Table
    table = Table(title="📊 Sektör Bazlı Sermaye Rotasyonu Sıralaması", border_style="blue", show_lines=True)
    table.add_column("Sıra", justify="center", style="bold", width=4)
    table.add_column("Sektör", style="bold white", width=24)
    table.add_column("Net Para Akımı ($)", justify="right", width=18)
    table.add_column("Alıcı Oranı (%)", justify="center", width=15)
    table.add_column("Ort. Fiyat Değ.", justify="right", width=15)
    table.add_column("Toplam Hacim ($)", justify="right", width=16)
    table.add_column("Sektör Lideri (MVP)", justify="left", width=22)
    table.add_column("Durum", justify="center", width=16)

    for idx, sec in enumerate(sector_results, 1):
        net_inflow = sec["net_inflow_usdt"]
        buy_ratio = sec["buy_ratio_pct"]
        avg_change = sec["avg_price_change_pct"]
        total_vol = sec["total_volume_usdt"]
        mvp = f"{sec['mvp_symbol']} (+${sec['mvp_net_inflow']:,.0f})"

        # Color coding
        if net_inflow > 0:
            inflow_str = f"[bold green]+${net_inflow:,.0f}[/bold green]"
            ratio_str = f"[green]%{buy_ratio:.1f} Alıcı[/green]"
        else:
            inflow_str = f"[bold red]-${abs(net_inflow):,.0f}[/bold red]"
            ratio_str = f"[red]%{100 - buy_ratio:.1f} Satıcı[/red]"

        price_str = f"[green]+%{avg_change:.2f}[/green]" if avg_change > 0 else f"[red]-%{abs(avg_change):.2f}[/red]"
        vol_str = f"${total_vol:,.0f}"

        table.add_row(
            str(idx),
            sec["sector"],
            inflow_str,
            ratio_str,
            price_str,
            vol_str,
            mvp,
            sec["sentiment"]
        )

    console.print(table)

    # Signals Panel
    if signals:
        sig_panel = Table(title="🚨 Canlı Algoritmik Sinyaller & Para Girişi Uyarıları", border_style="yellow")
        sig_panel.add_column("Sinyal Türü", style="bold yellow", width=28)
        sig_panel.add_column("Sektör", style="bold white", width=24)
        sig_panel.add_column("Detay / Açıklama", style="white")

        for sig in signals:
            sig_panel.add_row(
                sig["type"],
                sig["sector"],
                sig["message"]
            )
        console.print(sig_panel)

    console.print("[dim italic]Yenilemek için bekleniyor... (Durdurmak için Ctrl+C)[/dim italic]\n")

def main():
    parser = argparse.ArgumentParser(description="Real-Time Crypto Sector Flow Monitor")
    parser.add_argument("--timeframe", type=str, default="1h", choices=["15m", "1h", "4h"], help="Scanning timeframe")
    parser.add_argument("--once", action="store_true", help="Run once and exit without looping")
    parser.add_argument("--interval", type=int, default=20, help="Refresh interval in seconds (default 20)")
    args = parser.parse_args()

    engine = SectorFlowEngine()
    detector = SectorAnomalyDetector()

    if args.once:
        console.print(f"[bold cyan]Tek seferlik tarama başlatılıyor ({args.timeframe})...[/bold cyan]")
        results = engine.scan_all_sectors(timeframe=args.timeframe)
        signals = detector.detect_signals(results)
        render_screen(results, signals, timeframe=args.timeframe)
        return

    try:
        while True:
            console.clear()
            results = engine.scan_all_sectors(timeframe=args.timeframe)
            signals = detector.detect_signals(results)
            render_screen(results, signals, timeframe=args.timeframe)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]İzleme sonlandırıldı.[/yellow]")

if __name__ == "__main__":
    main()
