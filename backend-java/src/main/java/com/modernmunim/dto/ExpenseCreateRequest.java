package com.modernmunim.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record ExpenseCreateRequest(
        @NotBlank String category,
        @NotBlank String description,
        @NotNull BigDecimal amount,
        String expenseType,
        Integer productId
) {
    public ExpenseCreateRequest {
        if (expenseType == null || expenseType.isBlank()) {
            expenseType = "one_time";
        }
    }
}
