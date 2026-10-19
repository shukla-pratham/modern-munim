package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;

public record DashboardSalesResponse(
        Integer totalSales,
        BigDecimal totalRevenue,
        List<ProductSales> salesByProduct,
        List<SalesOverTime> salesOverTime
) {
    public record ProductSales(
            Integer productId,
            String name,
            Integer quantitySold,
            BigDecimal revenue
    ) {}

    public record SalesOverTime(
            String date,
            Integer orders,
            BigDecimal revenue
    ) {}
}
