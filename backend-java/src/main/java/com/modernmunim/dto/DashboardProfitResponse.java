package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;

public record DashboardProfitResponse(
        BigDecimal totalRevenue,
        BigDecimal totalExpenses,
        BigDecimal netProfit,
        BigDecimal profitMargin,
        List<ProductProfit> profitByProduct
) {
    public record ProductProfit(
            Integer productId,
            String productName,
            BigDecimal revenue,
            BigDecimal expenses,
            BigDecimal profit,
            BigDecimal margin
    ) {}
}
