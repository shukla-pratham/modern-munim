package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

public record PurchaseOrderItemResponse(
        Integer productId,
        String productName,
        Integer quantity,
        BigDecimal unitCost,
        BigDecimal totalCost
) {}
