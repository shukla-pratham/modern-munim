package com.modernmunim.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record ProductCreateRequest(
        @NotBlank String name,
        String description,
        @NotNull @DecimalMin(value = "0.0", inclusive = true) BigDecimal price,
        @Min(0) Integer stockQuantity,
        @Min(0) Integer stockThreshold
) {
    public ProductCreateRequest {
        if (stockQuantity == null) {
            stockQuantity = 0;
        }
        if (stockThreshold == null) {
            stockThreshold = 10;
        }
    }
}
