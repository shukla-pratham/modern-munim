package com.modernmunim.dto;

import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record PurchaseOrderItemCreateRequest(
        @NotNull Integer productId,
        @NotNull Integer quantity,
        @NotNull BigDecimal unitCost
) {}
