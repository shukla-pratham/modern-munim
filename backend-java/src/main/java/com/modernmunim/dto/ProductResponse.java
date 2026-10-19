package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record ProductResponse(
        Integer id,
        String name,
        String description,
        BigDecimal price,
        Integer stockQuantity,
        Integer stockThreshold,
        OffsetDateTime createdAt,
        OffsetDateTime updatedAt
) {}
