package com.modernmunim.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;

import java.math.BigDecimal;

public record ProductUpdateRequest(
        String name,
        String description,
        @DecimalMin(value = "0.0", inclusive = true) BigDecimal price,
        @Min(0) Integer stockThreshold
) {}
