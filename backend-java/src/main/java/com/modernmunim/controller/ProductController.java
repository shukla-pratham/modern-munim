package com.modernmunim.controller;

import com.modernmunim.dto.ProductCreateRequest;
import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.ProductUpdateRequest;
import com.modernmunim.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.util.List;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
@Validated
@Tag(name = "Products")
public class ProductController {

    private final ProductService productService;

    @GetMapping
    @Operation(summary = "List products (public)")
    public List<ProductResponse> list(
            @RequestParam(defaultValue = "0") @Min(0) int skip,
            @RequestParam(defaultValue = "100") @Min(1) @Max(100) int limit,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) @Min(0) BigDecimal minPrice,
            @RequestParam(required = false) @Min(0) BigDecimal maxPrice,
            @RequestParam(defaultValue = "false") boolean inStockOnly
    ) {
        return productService.listProducts(skip, limit, search, minPrice, maxPrice, inStockOnly);
    }

    @GetMapping("/{productId}")
    @Operation(summary = "Get product by id (public)")
    public ProductResponse get(@PathVariable Integer productId) {
        return productService.getProduct(productId);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create product (admin)", security = @SecurityRequirement(name = "bearerAuth"))
    public ProductResponse create(@Valid @RequestBody ProductCreateRequest request) {
        return productService.createProduct(request);
    }

    @PutMapping("/{productId}")
    @Operation(summary = "Update product (admin)", security = @SecurityRequirement(name = "bearerAuth"))
    public ProductResponse update(
            @PathVariable Integer productId,
            @Valid @RequestBody ProductUpdateRequest request
    ) {
        return productService.updateProduct(productId, request);
    }

    @DeleteMapping("/{productId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete product (admin)", security = @SecurityRequirement(name = "bearerAuth"))
    public void delete(@PathVariable Integer productId) {
        productService.deleteProduct(productId);
    }
}
