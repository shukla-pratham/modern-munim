package com.modernmunim.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public record StockMovementRequest(
        @NotNull Integer productId,
        @NotNull @Min(1) Integer quantity,
        String reason
) {}
