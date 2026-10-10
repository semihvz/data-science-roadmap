#include "simulator/indexing/SegmentTree.hpp"

namespace simulator::indexing {

void SegmentTree::build(const double* highArray, const double* lowArray, int32_t size) {
    n_ = size;
    if (n_ <= 0) return;
    tree_max_high_.assign(4 * n_, -std::numeric_limits<double>::infinity());
    tree_min_low_.assign(4 * n_, std::numeric_limits<double>::infinity());
    buildImpl(1, 0, n_ - 1, highArray, lowArray);
}

void SegmentTree::buildImpl(int32_t node, int32_t l, int32_t r, const double* highArray, const double* lowArray) {
    if (l == r) {
        tree_max_high_[node] = highArray[l];
        tree_min_low_[node] = lowArray[l];
        return;
    }
    int32_t mid = l + (r - l) / 2;
    buildImpl(2 * node, l, mid, highArray, lowArray);
    buildImpl(2 * node + 1, mid + 1, r, highArray, lowArray);
    tree_max_high_[node] = std::max(tree_max_high_[2 * node], tree_max_high_[2 * node + 1]);
    tree_min_low_[node] = std::min(tree_min_low_[2 * node], tree_min_low_[2 * node + 1]);
}

int32_t SegmentTree::findFirstHighGe(int32_t L, int32_t R, double target) const {
    if (n_ <= 0 || L > R || L >= n_ || R < 0) return -1;
    L = std::max(0, L);
    R = std::min(n_ - 1, R);
    return findFirstHighGeImpl(1, 0, n_ - 1, L, R, target);
}

int32_t SegmentTree::findFirstHighGeImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R, double target) const {
    if (l > R || r < L || tree_max_high_[node] < target) {
        return -1;
    }
    if (l == r) {
        return l;
    }
    int32_t mid = l + (r - l) / 2;
    int32_t resLeft = findFirstHighGeImpl(2 * node, l, mid, L, R, target);
    if (resLeft != -1) return resLeft;
    return findFirstHighGeImpl(2 * node + 1, mid + 1, r, L, R, target);
}

int32_t SegmentTree::findFirstLowLe(int32_t L, int32_t R, double target) const {
    if (n_ <= 0 || L > R || L >= n_ || R < 0) return -1;
    L = std::max(0, L);
    R = std::min(n_ - 1, R);
    return findFirstLowLeImpl(1, 0, n_ - 1, L, R, target);
}

int32_t SegmentTree::findFirstLowLeImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R, double target) const {
    if (l > R || r < L || tree_min_low_[node] > target) {
        return -1;
    }
    if (l == r) {
        return l;
    }
    int32_t mid = l + (r - l) / 2;
    int32_t resLeft = findFirstLowLeImpl(2 * node, l, mid, L, R, target);
    if (resLeft != -1) return resLeft;
    return findFirstLowLeImpl(2 * node + 1, mid + 1, r, L, R, target);
}

double SegmentTree::queryMaxHigh(int32_t L, int32_t R) const {
    if (n_ <= 0 || L > R || L >= n_ || R < 0) return -std::numeric_limits<double>::infinity();
    L = std::max(0, L);
    R = std::min(n_ - 1, R);
    return queryMaxHighImpl(1, 0, n_ - 1, L, R);
}

double SegmentTree::queryMaxHighImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R) const {
    if (l > R || r < L) return -std::numeric_limits<double>::infinity();
    if (L <= l && r <= R) return tree_max_high_[node];
    int32_t mid = l + (r - l) / 2;
    return std::max(queryMaxHighImpl(2 * node, l, mid, L, R),
                    queryMaxHighImpl(2 * node + 1, mid + 1, r, L, R));
}

double SegmentTree::queryMinLow(int32_t L, int32_t R) const {
    if (n_ <= 0 || L > R || L >= n_ || R < 0) return std::numeric_limits<double>::infinity();
    L = std::max(0, L);
    R = std::min(n_ - 1, R);
    return queryMinLowImpl(1, 0, n_ - 1, L, R);
}

double SegmentTree::queryMinLowImpl(int32_t node, int32_t l, int32_t r, int32_t L, int32_t R) const {
    if (l > R || r < L) return std::numeric_limits<double>::infinity();
    if (L <= l && r <= R) return tree_min_low_[node];
    int32_t mid = l + (r - l) / 2;
    return std::min(queryMinLowImpl(2 * node, l, mid, L, R),
                    queryMinLowImpl(2 * node + 1, mid + 1, r, L, R));
}

} // namespace simulator::indexing
