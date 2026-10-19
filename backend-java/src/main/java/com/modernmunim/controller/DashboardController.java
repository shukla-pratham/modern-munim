package com.modernmunim.controller;

import com.modernmunim.dto.DashboardExpenseBreakdownResponse;
import com.modernmunim.dto.DashboardProfitResponse;
import com.modernmunim.dto.DashboardRevenueResponse;
import com.modernmunim.dto.DashboardSalesResponse;
import com.modernmunim.dto.DashboardStockStatusResponse;
import com.modernmunim.service.DashboardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
@Validated
@Tag(name = "Dashboard")
@SecurityRequirement(name = "bearerAuth")
public class DashboardController {

    private final DashboardService dashboardService;

    @GetMapping("/revenue")
    @Operation(summary = "Revenue totals and daily breakdown (admin, read-only)")
    public DashboardRevenueResponse revenue(
            @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days
    ) {
        return dashboardService.revenue(days);
    }

    @GetMapping("/expenses")
    @Operation(summary = "Expense breakdown by category, type, and month (admin, read-only)")
    public DashboardExpenseBreakdownResponse expenses(
            @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days
    ) {
        return dashboardService.expenses(days);
    }

    @GetMapping("/profit")
    @Operation(summary = "Net profit and product-level margins (admin, read-only)")
    public DashboardProfitResponse profit(
            @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days
    ) {
        return dashboardService.profit(days);
    }

    @GetMapping("/stock-status")
    @Operation(summary = "Catalog stock counts, low/out-of-stock lists, inventory value (admin, read-only)")
    public DashboardStockStatusResponse stockStatus() {
        return dashboardService.stockStatus();
    }

    @GetMapping("/sales")
    @Operation(summary = "Completed sales counts, product totals, and daily sales (admin, read-only)")
    public DashboardSalesResponse sales(
            @RequestParam(defaultValue = "30") @Min(1) @Max(365) int days
    ) {
        return dashboardService.sales(days);
    }
}
