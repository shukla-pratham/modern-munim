package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record VendorPerformanceResponse(
        Integer vendorId,
        String vendorName,
        OffsetDateTime metricDate,
        BigDecimal avgLeadTime,
        BigDecimal onTimeDeliveryRate,
        BigDecimal fulfillmentRate,
        BigDecimal avgUnitCost,
        BigDecimal priceVariance,
        BigDecimal delayDaysAvg
) {}
