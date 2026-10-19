package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;

public record DashboardStockStatusResponse(
        Integer totalProducts,
        List<StockProduct> lowStockProducts,
        List<StockProduct> outOfStockProducts,
        BigDecimal stockValue
) {
    public record StockProduct(
            Integer productId,
            String name,
            Integer stockQuantity,
            Integer threshold
    ) {}
}
