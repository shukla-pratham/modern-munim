package com.modernmunim.dto;

import jakarta.validation.constraints.NotBlank;

import java.math.BigDecimal;

public record VendorCreateRequest(
        @NotBlank String name,
        Boolean isActive,
        Integer avgLeadTimeDays,
        BigDecimal reliabilityScore,
        BigDecimal costScore,
        BigDecimal overallScore
) {
    public VendorCreateRequest {
        if (isActive == null) {
            isActive = true;
        }
    }
}
