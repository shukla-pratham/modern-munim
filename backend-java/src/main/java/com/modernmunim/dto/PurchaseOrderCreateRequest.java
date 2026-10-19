package com.modernmunim.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.time.OffsetDateTime;
import java.util.List;

public record PurchaseOrderCreateRequest(
        @NotNull Integer vendorId,
        @NotNull @Valid List<PurchaseOrderItemCreateRequest> items,
        OffsetDateTime promisedDeliveryDate
) {}
