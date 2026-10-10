#include "simulator/indexing/SegmentTree.hpp"
#include <cassert>
#include <iostream>
#include <vector>

using namespace simulator;

void testSegmentTreeQueries() {
    std::vector<double> highs = {105.0, 110.0, 108.0, 120.0, 115.0};
    std::vector<double> lows  = {95.0,  98.0,  92.0,  105.0, 100.0};

    indexing::SegmentTree segTree;
    segTree.build(highs.data(), lows.data(), 5);

    // Test findFirstHighGe
    int32_t idxHigh = segTree.findFirstHighGe(0, 4, 110.0);
    assert(idxHigh == 1);

    int32_t idxHigh2 = segTree.findFirstHighGe(2, 4, 118.0);
    assert(idxHigh2 == 3);

    // Test findFirstLowLe
    int32_t idxLow = segTree.findFirstLowLe(0, 4, 95.0);
    assert(idxLow == 0);

    int32_t idxLow2 = segTree.findFirstLowLe(1, 4, 93.0);
    assert(idxLow2 == 2);

    // Test Range Queries
    double maxH = segTree.queryMaxHigh(1, 3);
    assert(maxH == 120.0);

    double minL = segTree.queryMinLow(0, 2);
    assert(minL == 92.0);

    std::cout << "[PASS] testSegmentTreeQueries" << std::endl;
}

int main() {
    testSegmentTreeQueries();
    std::cout << "SegmentTree tests passed successfully!" << std::endl;
    return 0;
}
