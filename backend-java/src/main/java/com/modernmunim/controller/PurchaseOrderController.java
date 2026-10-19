package com.modernmunim.controller;

import com.modernmunim.dto.PurchaseOrderCreateRequest;
import com.modernmunim.dto.PurchaseOrderResponse;
import com.modernmunim.service.PurchaseOrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/purchase-orders")
@RequiredArgsConstructor
@Tag(name = "Purchase Orders")
@SecurityRequirement(name = "bearerAuth")
public class PurchaseOrderController {

    private final PurchaseOrderService purchaseOrderService;

    @PostMapping
    @Operation(summary = "Create purchase order (admin); does not mutate inventory")
    public PurchaseOrderResponse create(@Valid @RequestBody PurchaseOrderCreateRequest request) {
        return purchaseOrderService.create(request);
    }

    @GetMapping
    @Operation(summary = "List purchase orders (admin), optional vendor_id filter, max 100")
    public List<PurchaseOrderResponse> list(@RequestParam(name = "vendor_id", required = false) Integer vendorId) {
        return purchaseOrderService.list(vendorId);
    }

    @PostMapping("/{id}/deliver")
    @Operation(summary = "Mark purchase order delivered (admin); stock-in + ledger atomically")
    public PurchaseOrderResponse deliver(
            @PathVariable Integer id,
            @RequestParam(required = false) OffsetDateTime actualDeliveryDate
    ) {
        return purchaseOrderService.deliver(id, actualDeliveryDate);
    }
}
