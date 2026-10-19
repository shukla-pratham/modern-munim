package com.modernmunim.controller;

import com.modernmunim.dto.BestVendorResponse;
import com.modernmunim.dto.VendorComparisonResponse;
import com.modernmunim.dto.VendorCreateRequest;
import com.modernmunim.dto.VendorCreateResponse;
import com.modernmunim.dto.VendorPerformanceResponse;
import com.modernmunim.dto.VendorProductCreateRequest;
import com.modernmunim.dto.VendorProductResponse;
import com.modernmunim.dto.VendorRankingResponse;
import com.modernmunim.dto.VendorScorecardResponse;
import com.modernmunim.service.VendorService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.util.List;

@RestController
@RequestMapping("/api/vendors")
@RequiredArgsConstructor
@Validated
@Tag(name = "Vendors")
@SecurityRequirement(name = "bearerAuth")
public class VendorController {

    private final VendorService vendorService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create vendor (admin)")
    public VendorCreateResponse create(@Valid @RequestBody VendorCreateRequest request) {
        return vendorService.create(request);
    }

    @DeleteMapping("/{vendorId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete vendor (admin); blocked if purchase orders exist")
    public void delete(@PathVariable Integer vendorId) {
        vendorService.delete(vendorId);
    }

    @GetMapping("/rankings")
    @Operation(summary = "Ranked active vendors (admin); SPA vendor list")
    public List<VendorRankingResponse> rankings(
            @RequestParam(name = "product_id", required = false) Integer productId,
            @RequestParam(name = "min_reliability", required = false)
            @DecimalMin("0") @DecimalMax("100") BigDecimal minReliability,
            @RequestParam(name = "max_cost", required = false)
            @DecimalMin("0") BigDecimal maxCost
    ) {
        return vendorService.rankings(productId, minReliability, maxCost);
    }

    @GetMapping("/best-for-product/{productId}")
    @Operation(summary = "Best vendor for a product (admin)")
    public BestVendorResponse bestForProduct(@PathVariable Integer productId) {
        return vendorService.bestForProduct(productId);
    }

    @GetMapping("/compare-for-product/{productId}")
    @Operation(summary = "Compare vendors for a product (admin)")
    public List<VendorComparisonResponse> compareForProduct(@PathVariable Integer productId) {
        return vendorService.compareForProduct(productId);
    }

    @GetMapping("/{vendorId}/performance")
    @Operation(summary = "Vendor performance history (admin)")
    public List<VendorPerformanceResponse> performance(
            @PathVariable Integer vendorId,
            @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days
    ) {
        return vendorService.performance(vendorId, days);
    }

    @GetMapping("/{vendorId}/products")
    @Operation(summary = "Products supplied by an active vendor (admin)")
    public List<VendorProductResponse> vendorProducts(@PathVariable Integer vendorId) {
        return vendorService.listVendorProducts(vendorId);
    }

    @PostMapping("/{vendorId}/products")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Add a product to a vendor catalog (admin)")
    public VendorProductResponse addProduct(
            @PathVariable Integer vendorId,
            @Valid @RequestBody VendorProductCreateRequest request
    ) {
        return vendorService.addProduct(vendorId, request);
    }

    @GetMapping("/{vendorId}/scorecard")
    @Operation(summary = "Vendor scorecard (admin)")
    public VendorScorecardResponse scorecard(@PathVariable Integer vendorId) {
        return vendorService.scorecard(vendorId);
    }
}
