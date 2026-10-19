package com.modernmunim.dto;

import java.math.BigDecimal;

public record VendorComparisonResponse(
        Integer vendorId,
        String vendorName,
        BigDecimal unitCost,
        BigDecimal reliabilityScore,
        Integer leadTimeDays,
        BigDecimal riskScore,
        BigDecimal overallScore
) {}
