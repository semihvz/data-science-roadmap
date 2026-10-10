from flow_calculator import fetch_symbol_derivatives_info

class SectorAnomalyDetector:
    def __init__(self, inflow_ratio_threshold=55.0, net_inflow_min_usd=500_000):
        self.inflow_ratio_threshold = inflow_ratio_threshold
        self.net_inflow_min_usd = net_inflow_min_usd

    def detect_signals(self, sector_results):
        """
        Analyzes sector results to generate actionable intelligence signals.
        """
        signals = []

        for sec in sector_results:
            net_inflow = sec["net_inflow_usdt"]
            buy_ratio = sec["buy_ratio_pct"]
            total_vol = sec["total_volume_usdt"]
            mvp = sec["mvp_symbol"]
            mvp_inflow = sec["mvp_net_inflow"]

            # Signal 1: Heavy Inflow Aggression
            if net_inflow >= self.net_inflow_min_usd and buy_ratio >= self.inflow_ratio_threshold:
                signals.append({
                    "type": "🚀 GÜÇLÜ SERMAYE GİRİŞİ",
                    "sector": sec["sector"],
                    "severity": "HIGH",
                    "message": f"{sec['sector']} sektörüne son 1 saatte net +${net_inflow:,.0f} girdi! Alıcı baskısı: %{buy_ratio:.1f}.",
                    "lead_token": mvp,
                    "lead_token_inflow": mvp_inflow
                })

            # Signal 2: Heavy Outflow / Distribution
            elif net_inflow <= -self.net_inflow_min_usd and buy_ratio <= (100 - self.inflow_ratio_threshold):
                signals.append({
                    "type": "⚠️ AGRESİF SATIŞ / ÇIKIŞ",
                    "sector": sec["sector"],
                    "severity": "HIGH",
                    "message": f"{sec['sector']} sektöründen net -${abs(net_inflow):,.0f} sermaye çıktı! Satıcı baskısı: %{100 - buy_ratio:.1f}.",
                    "lead_token": sec["laggard_symbol"],
                    "lead_token_inflow": sec["laggard_net_inflow"]
                })

            # Signal 3: Concentrated Sector MVP (Single token taking majority of sector inflow)
            if net_inflow > 0 and (mvp_inflow / net_inflow) > 0.65 and len(sec["symbols_details"]) > 2:
                signals.append({
                    "type": "🎯 TEK TOKEN ODAKLI ROTASYON",
                    "sector": sec["sector"],
                    "severity": "MEDIUM",
                    "message": f"{sec['sector']} sektöründeki net para girişinin %{(mvp_inflow / net_inflow * 100):.1f}'i tek başına {mvp} tarafından çekiliyor!",
                    "lead_token": mvp,
                    "lead_token_inflow": mvp_inflow
                })

        return signals
