package com.modernmunim.controller;

import com.modernmunim.dto.ExpenseCreateRequest;
import com.modernmunim.dto.ExpenseResponse;
import com.modernmunim.dto.ExpenseUpdateRequest;
import com.modernmunim.service.ExpenseService;
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

import java.util.List;

@RestController
@RequestMapping("/api/expenses")
@RequiredArgsConstructor
@Validated
@Tag(name = "Expenses")
@SecurityRequirement(name = "bearerAuth")
public class ExpenseController {

    private final ExpenseService expenseService;

    @GetMapping
    @Operation(summary = "List expenses (admin)")
    public List<ExpenseResponse> list(
            @RequestParam(defaultValue = "0") @Min(0) int skip,
            @RequestParam(defaultValue = "100") @Min(1) @Max(100) int limit,
            @RequestParam(required = false) String category,
            @RequestParam(name = "product_id", required = false) Integer productId
    ) {
        return expenseService.list(skip, limit, category, productId);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create expense (admin)")
    public ExpenseResponse create(@Valid @RequestBody ExpenseCreateRequest request) {
        return expenseService.create(request);
    }

    @PutMapping("/{expenseId}")
    @Operation(summary = "Update expense (admin)")
    public ExpenseResponse update(
            @PathVariable Integer expenseId,
            @Valid @RequestBody ExpenseUpdateRequest request
    ) {
        return expenseService.update(expenseId, request);
    }

    @DeleteMapping("/{expenseId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete expense (admin)")
    public void delete(@PathVariable Integer expenseId) {
        expenseService.delete(expenseId);
    }
}
