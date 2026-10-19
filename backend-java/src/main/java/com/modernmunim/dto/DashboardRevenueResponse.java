package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;

public record DashboardRevenueResponse(
        BigDecimal totalRevenue,
        String period,
        List<DailyRevenue> dailyRevenue
) {
    public record DailyRevenue(String date, BigDecimal revenue) {}
}
