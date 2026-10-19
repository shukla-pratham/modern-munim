package com.modernmunim.controller;

import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.StockMovementRequest;
import com.modernmunim.dto.StockTransactionResponse;
import com.modernmunim.dto.ThresholdUpdateRequest;
import com.modernmunim.service.InventoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/inventory")
@RequiredArgsConstructor
@Validated
@Tag(name = "Inventory")
@SecurityRequirement(name = "bearerAuth")
public class InventoryController {

    private final InventoryService inventoryService;

    @PostMapping("/stock-in")
    @Operation(summary = "Add stock (admin)")
    public StockTransactionResponse stockIn(@Valid @RequestBody StockMovementRequest request) {
        return inventoryService.stockIn(request.productId(), request.quantity(), request.reason());
    }

    @PostMapping("/stock-out")
    @Operation(summary = "Remove stock (admin)")
    public StockTransactionResponse stockOut(@Valid @RequestBody StockMovementRequest request) {
        return inventoryService.stockOut(request.productId(), request.quantity(), request.reason());
    }

    @GetMapping("/transactions")
    @Operation(summary = "List stock transactions (admin)")
    public List<StockTransactionResponse> transactions(
            @RequestParam(required = false) Integer productId,
            @RequestParam(defaultValue = "0") @Min(0) int skip,
            @RequestParam(defaultValue = "100") @Min(1) @Max(100) int limit
    ) {
        return inventoryService.listTransactions(productId, skip, limit);
    }

    @PutMapping("/products/{productId}/threshold")
    @Operation(summary = "Update stock threshold (admin)")
    public ProductResponse updateThreshold(
            @PathVariable Integer productId,
            @Valid @RequestBody ThresholdUpdateRequest request
    ) {
        return inventoryService.updateThreshold(productId, request.stockThreshold());
    }
}
