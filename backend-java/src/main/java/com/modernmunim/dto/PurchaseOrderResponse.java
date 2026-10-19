package com.modernmunim.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

public record PurchaseOrderResponse(
        Integer id,
        Integer vendorId,
        String vendorName,
        String poNumber,
        String status,
        BigDecimal totalCost,
        OffsetDateTime orderDate,
        OffsetDateTime promisedDeliveryDate,
        OffsetDateTime actualDeliveryDate,
        Integer delayDays,
        List<PurchaseOrderItemResponse> items
) {}
