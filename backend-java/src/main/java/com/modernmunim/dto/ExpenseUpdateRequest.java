package com.modernmunim.dto;

import java.math.BigDecimal;

/**
 * Null fields mean "leave unchanged" (mirrors FastAPI exclude_unset for omitted keys).
 * Explicit JSON null also leaves unchanged — clearing product_id via null is not supported
 * (documented FastAPI parity gap).
 */
public record ExpenseUpdateRequest(
        String category,
        String description,
        BigDecimal amount,
        String expenseType,
        Integer productId
) {}
