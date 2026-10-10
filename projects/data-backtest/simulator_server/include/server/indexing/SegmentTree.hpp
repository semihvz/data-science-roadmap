#pragma once

#include <vector>
#include <cstdint>
#include <algorithm>
#include <limits>

namespace server::indexing {

class SegmentTree {
public:
    SegmentTree() = default;

    void build(const double* highArray, const double* lowArray, int32_t size);
    int32_t findFirstHighGe(int32_t L, int32_t R, double target) const;
    int32_t findFirstLowLe(int32_t L, int32_t R, double target) const;
    double queryMaxHigh(int32_t L, int32_t R) const;
    double queryMinLow(int32_t L, int32_t R) const;

private:
    int32_t n_ = 0;
    std::vector<double> tree_max_high_;
    std::vector<double> tree_min_low_;

    void buildImpl(int32_t node, int32_t l, int32_t r, const double* highArray, const double* lowArray);
    int32_t findFirstHighGeImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R, double target) const;
    int32_t findFirstLowLeImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R, double target) const;
    double queryMaxHighImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R) const;
    double queryMinLowImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R) const;
};

} // namespace server::indexing
