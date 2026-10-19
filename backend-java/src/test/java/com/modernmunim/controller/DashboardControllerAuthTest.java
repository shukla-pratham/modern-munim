package com.modernmunim.controller;

import com.modernmunim.dto.DashboardExpenseBreakdownResponse;
import com.modernmunim.dto.DashboardProfitResponse;
import com.modernmunim.dto.DashboardRevenueResponse;
import com.modernmunim.dto.DashboardSalesResponse;
import com.modernmunim.dto.DashboardStockStatusResponse;
import com.modernmunim.exception.GlobalExceptionHandler;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtAuthenticationFilter;
import com.modernmunim.security.JwtService;
import com.modernmunim.security.SecurityConfig;
import com.modernmunim.security.SecurityErrorHandlers;
import com.modernmunim.service.DashboardService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = DashboardController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityErrorHandlers.class, GlobalExceptionHandler.class})
class DashboardControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private DashboardService dashboardService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    @Test
    void unauthenticatedRevenueIs401() throws Exception {
        mockMvc.perform(get("/api/dashboard/revenue")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedExpensesIs401() throws Exception {
        mockMvc.perform(get("/api/dashboard/expenses")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedProfitIs401() throws Exception {
        mockMvc.perform(get("/api/dashboard/profit")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedStockStatusIs401() throws Exception {
        mockMvc.perform(get("/api/dashboard/stock-status")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedSalesIs401() throws Exception {
        mockMvc.perform(get("/api/dashboard/sales")).andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerRevenueIs403() throws Exception {
        mockMvc.perform(get("/api/dashboard/revenue")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerExpensesIs403() throws Exception {
        mockMvc.perform(get("/api/dashboard/expenses")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerProfitIs403() throws Exception {
        mockMvc.perform(get("/api/dashboard/profit")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerStockStatusIs403() throws Exception {
        mockMvc.perform(get("/api/dashboard/stock-status")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerSalesIs403() throws Exception {
        mockMvc.perform(get("/api/dashboard/sales")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminRevenueSuccessUsesSnakeCaseAndDefaultDays() throws Exception {
        when(dashboardService.revenue(30)).thenReturn(new DashboardRevenueResponse(
                new BigDecimal("0.00"), "last_30_days", List.of()));
        mockMvc.perform(get("/api/dashboard/revenue"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_revenue").value(0.00))
                .andExpect(jsonPath("$.period").value("last_30_days"))
                .andExpect(jsonPath("$.daily_revenue").isArray());
        verify(dashboardService).revenue(30);
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminExpensesSuccess() throws Exception {
        when(dashboardService.expenses(30)).thenReturn(new DashboardExpenseBreakdownResponse(
                new BigDecimal("0.00"),
                Map.of("inventory", new BigDecimal("0.00"), "operations", new BigDecimal("0.00"), "marketing", new BigDecimal("0.00")),
                Map.of("one_time", new BigDecimal("0.00"), "recurring", new BigDecimal("0.00")),
                List.of()));
        mockMvc.perform(get("/api/dashboard/expenses"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_expenses").value(0.00))
                .andExpect(jsonPath("$.by_category.inventory").value(0.00))
                .andExpect(jsonPath("$.by_type.one_time").value(0.00))
                .andExpect(jsonPath("$.monthly_expenses").isArray());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminProfitSuccess() throws Exception {
        when(dashboardService.profit(30)).thenReturn(new DashboardProfitResponse(
                new BigDecimal("0.00"), new BigDecimal("0.00"), new BigDecimal("0.00"),
                new BigDecimal("0.00"), List.of()));
        mockMvc.perform(get("/api/dashboard/profit"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_revenue").exists())
                .andExpect(jsonPath("$.net_profit").exists())
                .andExpect(jsonPath("$.profit_by_product").isArray());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminStockStatusSuccess() throws Exception {
        when(dashboardService.stockStatus()).thenReturn(new DashboardStockStatusResponse(
                0, List.of(), List.of(), new BigDecimal("0.00")));
        mockMvc.perform(get("/api/dashboard/stock-status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_products").value(0))
                .andExpect(jsonPath("$.low_stock_products").isArray())
                .andExpect(jsonPath("$.out_of_stock_products").isArray())
                .andExpect(jsonPath("$.stock_value").value(0.00));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminSalesSuccess() throws Exception {
        when(dashboardService.sales(30)).thenReturn(new DashboardSalesResponse(
                0, new BigDecimal("0.00"), List.of(), List.of()));
        mockMvc.perform(get("/api/dashboard/sales"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total_sales").value(0))
                .andExpect(jsonPath("$.sales_by_product").isArray())
                .andExpect(jsonPath("$.sales_over_time").isArray());
    }

    @ParameterizedTest
    @ValueSource(ints = {1, 30, 365})
    @WithMockUser(roles = "ADMIN")
    void adminAcceptedDaysValues(int days) throws Exception {
        when(dashboardService.revenue(days)).thenReturn(new DashboardRevenueResponse(
                new BigDecimal("0.00"), "last_" + days + "_days", List.of()));
        mockMvc.perform(get("/api/dashboard/revenue").param("days", String.valueOf(days)))
                .andExpect(status().isOk());
        verify(dashboardService).revenue(days);
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 366, -1})
    @WithMockUser(roles = "ADMIN")
    void invalidDaysRejected(int days) throws Exception {
        mockMvc.perform(get("/api/dashboard/revenue").param("days", String.valueOf(days)))
                .andExpect(status().isUnprocessableEntity());
    }
}
