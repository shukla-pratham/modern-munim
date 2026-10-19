package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

public record OrderResponse(
        Integer id,
        Integer userId,
        BigDecimal totalAmount,
        String status,
        OffsetDateTime createdAt,
        List<OrderItemResponse> items
) {}
