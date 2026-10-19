package com.modernmunim.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

public record VendorCreateResponse(
        Integer id,
        String name,
        @JsonProperty("is_active") Boolean isActive,
        Integer avgLeadTimeDays,
        BigDecimal reliabilityScore,
        BigDecimal costScore,
        BigDecimal overallScore
) {}
