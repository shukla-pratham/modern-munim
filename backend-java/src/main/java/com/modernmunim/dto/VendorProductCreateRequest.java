package com.modernmunim.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record VendorProductCreateRequest(
        @NotNull Integer productId,
        @NotNull BigDecimal unitCost,
        Integer minOrderQty,
        Integer leadTimeDays
) {
    public VendorProductCreateRequest {
        if (minOrderQty == null) {
            minOrderQty = 1;
        }
    }
}
