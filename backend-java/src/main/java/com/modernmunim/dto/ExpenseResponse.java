package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record ExpenseResponse(
        Integer id,
        String category,
        String description,
        BigDecimal amount,
        String expenseType,
        Integer productId,
        String productName,
        OffsetDateTime createdAt
) {}
