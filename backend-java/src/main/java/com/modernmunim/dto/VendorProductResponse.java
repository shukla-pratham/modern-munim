package com.modernmunim.dto;

import java.math.BigDecimal;

public record VendorProductResponse(
        Integer vendorProductId,
        Integer productId,
        String productName,
        BigDecimal unitCost,
        Integer minOrderQty,
        Integer leadTimeDays
) {}
