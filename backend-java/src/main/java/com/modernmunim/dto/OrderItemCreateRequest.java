package com.modernmunim.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public record OrderItemCreateRequest(
        @NotNull Integer productId,
        @NotNull @Min(1) Integer quantity
) {}
