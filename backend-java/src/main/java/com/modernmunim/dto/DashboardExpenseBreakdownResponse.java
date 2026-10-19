package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public record DashboardExpenseBreakdownResponse(
        BigDecimal totalExpenses,
        Map<String, BigDecimal> byCategory,
        Map<String, BigDecimal> byType,
        List<MonthlyAmount> monthlyExpenses
) {
    public record MonthlyAmount(String month, BigDecimal amount) {}
}
