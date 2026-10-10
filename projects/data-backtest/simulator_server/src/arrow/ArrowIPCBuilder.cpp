#include "server/arrow/ArrowIPCBuilder.hpp"
#include <sstream>
#include <cstring>
#include <cmath>
#include <limits>

namespace server::arrow {

std::string ArrowIPCBuilder::serializeToBinaryIPCStream(const std::vector<data::TradeResult>& trades) {
    std::ostringstream ss(std::ios::binary);
    uint32_t numRows = static_cast<uint32_t>(trades.size());
    uint32_t numCols = 48;

    ss.write("ARROW_STREAM", 12);
    ss.write(reinterpret_cast<const char*>(&numRows), sizeof(numRows));
    ss.write(reinterpret_cast<const char*>(&numCols), sizeof(numCols));

    if (numRows == 0) return ss.str();

    // Helper lambda for double Nan
    auto dNaN = [](double v) { return std::isnan(v) ? std::numeric_limits<double>::quiet_NaN() : v; };

    // Col 1: trade_id (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.trade_id; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 2: side (int8_t)
    for (const auto& tr : trades) { int8_t v = static_cast<int8_t>(tr.side); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 3: entry_bar_index (int32_t)
    for (const auto& tr : trades) { int32_t v = tr.entry_bar_index; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 4: exit_bar_index (int32_t)
    for (const auto& tr : trades) { int32_t v = tr.exit_bar_index; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 5: entry_bar_open_time (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.entry_bar_open_time; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 6: entry_time (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.entry_time; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 7: exit_bar_open_time (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.exit_bar_open_time; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 8: entry_price (double)
    for (const auto& tr : trades) { double v = tr.entry_price; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 9: exit_price (double)
    for (const auto& tr : trades) { double v = tr.status == data::PositionStatus::CLOSED ? tr.exit_price : std::numeric_limits<double>::quiet_NaN(); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 10: tp_price (double)
    for (const auto& tr : trades) { double v = tr.tp_price; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 11: sl_price (double)
    for (const auto& tr : trades) { double v = tr.sl_price; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 12: sl_percent (double)
    for (const auto& tr : trades) { double v = tr.sl_percent; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 13: tp_percent (double)
    for (const auto& tr : trades) { double v = tr.tp_percent; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 14: risk_reward_ratio (double)
    for (const auto& tr : trades) { double v = tr.risk_reward_ratio; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 15: status (int8_t)
    for (const auto& tr : trades) { int8_t v = static_cast<int8_t>(tr.status); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 16: exit_reason (int8_t)
    for (const auto& tr : trades) { int8_t v = static_cast<int8_t>(tr.exit_reason); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 17: bars_held (int32_t)
    for (const auto& tr : trades) { int32_t v = tr.bars_held; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 18: duration_lower_bound_seconds (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.duration_lower_bound_seconds; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 19: duration_upper_bound_seconds (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.duration_upper_bound_seconds; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 20: duration_minutes_approx (double)
    for (const auto& tr : trades) { double v = tr.duration_minutes_approx; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 21: nominal_r (double)
    for (const auto& tr : trades) { double v = tr.nominal_r; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 22: gross_pnl_percent (double)
    for (const auto& tr : trades) { double v = tr.gross_pnl_percent; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 23: net_pnl_percent (double)
    for (const auto& tr : trades) { double v = tr.net_pnl_percent; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 24: gross_pnl_r (double)
    for (const auto& tr : trades) { double v = tr.gross_pnl_r; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 25: net_pnl_r (double)
    for (const auto& tr : trades) { double v = tr.net_pnl_r; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 26: same_bar_sl_tp (uint8_t)
    for (const auto& tr : trades) { uint8_t v = tr.same_bar_sl_tp; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 27: intrabar_ambiguous (uint8_t)
    for (const auto& tr : trades) { uint8_t v = tr.intrabar_ambiguous; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 28: gap_through_barrier (uint8_t)
    for (const auto& tr : trades) { uint8_t v = tr.gap_through_barrier; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 29: data_segment_id (int32_t)
    for (const auto& tr : trades) { int32_t v = tr.data_segment_id; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 30: entry_candle_open (double)
    for (const auto& tr : trades) { double v = tr.entry_candle_open; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 31: entry_candle_high (double)
    for (const auto& tr : trades) { double v = tr.entry_candle_high; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 32: entry_candle_low (double)
    for (const auto& tr : trades) { double v = tr.entry_candle_low; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 33: entry_candle_close (double)
    for (const auto& tr : trades) { double v = tr.entry_candle_close; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 34: entry_candle_volume (double)
    for (const auto& tr : trades) { double v = tr.entry_candle_volume; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 35: exit_candle_open (double)
    for (const auto& tr : trades) { double v = tr.exit_candle_open; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 36: exit_candle_high (double)
    for (const auto& tr : trades) { double v = tr.exit_candle_high; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 37: exit_candle_low (double)
    for (const auto& tr : trades) { double v = tr.exit_candle_low; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 38: exit_candle_close (double)
    for (const auto& tr : trades) { double v = tr.exit_candle_close; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 39: exit_candle_volume (double)
    for (const auto& tr : trades) { double v = tr.exit_candle_volume; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 40: max_favorable_excursion_pct (double)
    for (const auto& tr : trades) { double v = tr.max_favorable_excursion_pct; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 41: max_adverse_excursion_pct (double)
    for (const auto& tr : trades) { double v = tr.max_adverse_excursion_pct; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 42: mfe_r (double)
    for (const auto& tr : trades) { double v = tr.mfe_r; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 43: mae_r (double)
    for (const auto& tr : trades) { double v = tr.mae_r; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 44: last_available_price (double)
    for (const auto& tr : trades) { double v = tr.status != data::PositionStatus::CLOSED ? tr.last_available_price : std::numeric_limits<double>::quiet_NaN(); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 45: last_available_timestamp (int64_t)
    for (const auto& tr : trades) { int64_t v = tr.last_available_timestamp; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 46: unrealized_pnl_pct (double)
    for (const auto& tr : trades) { double v = tr.status != data::PositionStatus::CLOSED ? tr.unrealized_pnl_pct : std::numeric_limits<double>::quiet_NaN(); ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 47: reserved_1 (int64_t)
    for (const auto& tr : trades) { int64_t v = 0; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }
    // Col 48: reserved_2 (int64_t)
    for (const auto& tr : trades) { int64_t v = 0; ss.write(reinterpret_cast<const char*>(&v), sizeof(v)); }

    return ss.str();
}

} // namespace server::arrow
