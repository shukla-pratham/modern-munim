package com.modernmunim.dto;

import java.time.OffsetDateTime;

public record StockTransactionResponse(
        Integer id,
        Integer productId,
        String productName,
        Integer quantityChange,
        String transactionType,
        String reason,
        OffsetDateTime createdAt
) {}
