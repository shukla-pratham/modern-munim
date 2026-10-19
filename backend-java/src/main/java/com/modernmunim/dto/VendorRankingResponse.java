package com.modernmunim.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

public record VendorRankingResponse(
        Integer vendorId,
        String vendorName,
        BigDecimal overallScore,
        BigDecimal reliabilityScore,
        BigDecimal costScore,
        Integer avgLeadTimeDays,
        @JsonProperty("is_active") Boolean isActive,
        String explanation
) {}
