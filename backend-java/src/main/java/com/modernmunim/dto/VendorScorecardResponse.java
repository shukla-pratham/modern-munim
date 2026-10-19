package com.modernmunim.dto;

import java.math.BigDecimal;
import java.util.List;

public record VendorScorecardResponse(
        Integer vendorId,
        String vendorName,
        BigDecimal currentReliability,
        String reliabilityTrend,
        BigDecimal currentCostScore,
        BigDecimal costVolatility,
        BigDecimal delayTrend,
        BigDecimal overallScore,
        List<String> actionInsights
) {}
