package com.modernmunim.service;

import com.modernmunim.dto.DashboardExpenseBreakdownResponse;
import com.modernmunim.dto.DashboardProfitResponse;
import com.modernmunim.dto.DashboardRevenueResponse;
import com.modernmunim.dto.DashboardSalesResponse;
import com.modernmunim.dto.DashboardStockStatusResponse;
import com.modernmunim.entity.ExpenseCategory;
import com.modernmunim.entity.ExpenseType;
import com.modernmunim.entity.OrderStatus;
import com.modernmunim.entity.Product;
import com.modernmunim.repository.ExpenseRepository;
import com.modernmunim.repository.OrderItemRepository;
import com.modernmunim.repository.OrderRepository;
import com.modernmunim.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.sql.Date;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.temporal.ChronoUnit;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DashboardServiceTest {

    private static final BigDecimal ZERO = new BigDecimal("0.00");

    @Mock
    private OrderRepository orderRepository;
    @Mock
    private OrderItemRepository orderItemRepository;
    @Mock
    private ExpenseRepository expenseRepository;
    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private DashboardService dashboardService;

    @BeforeEach
    void stubEmptyAggregations() {
        lenient().when(orderRepository.sumTotalAmountByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(ZERO);
        lenient().when(orderRepository.dailyRevenueByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(List.of());
        lenient().when(orderRepository.countByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(0L);
        lenient().when(orderRepository.dailySalesByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(List.of());
        lenient().when(orderItemRepository.aggregateProductSales(eq(OrderStatus.completed), any()))
                .thenReturn(List.of());
        lenient().when(expenseRepository.sumAmountSince(any())).thenReturn(ZERO);
        lenient().when(expenseRepository.sumAmountByCategorySince(any())).thenReturn(List.of());
        lenient().when(expenseRepository.sumAmountByTypeSince(any())).thenReturn(List.of());
        lenient().when(expenseRepository.sumAmountByMonthSince(any())).thenReturn(List.of());
        lenient().when(expenseRepository.sumAmountByProductSince(any())).thenReturn(List.of());
        lenient().when(productRepository.count()).thenReturn(0L);
        lenient().when(productRepository.sumInventoryValue()).thenReturn(ZERO);
        lenient().when(productRepository.findOutOfStock()).thenReturn(List.of());
        lenient().when(productRepository.findLowStock()).thenReturn(List.of());
    }

    @Test
    void revenueIncludesOnlyCompletedOrders() {
        when(orderRepository.sumTotalAmountByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(new BigDecimal("150.00"));
        when(orderRepository.dailyRevenueByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(rows(new Object[]{LocalDate.of(2026, 8, 1), new BigDecimal("150.00")}));

        DashboardRevenueResponse response = dashboardService.revenue(30);

        assertEquals(new BigDecimal("150.00"), response.totalRevenue());
        assertEquals("last_30_days", response.period());
        assertEquals(1, response.dailyRevenue().size());
        assertEquals("2026-08-01", response.dailyRevenue().getFirst().date());
        assertEquals(new BigDecimal("150.00"), response.dailyRevenue().getFirst().revenue());
        verify(orderRepository).sumTotalAmountByStatusSince(eq(OrderStatus.completed), any());
        verify(orderRepository, never()).sumTotalAmountByStatusSince(eq(OrderStatus.pending), any());
        verify(orderRepository, never()).sumTotalAmountByStatusSince(eq(OrderStatus.cancelled), any());
    }

    @Test
    void revenueEmptyResultIsZeroWithEmptyDailyList() {
        DashboardRevenueResponse response = dashboardService.revenue(30);
        assertEquals(ZERO, response.totalRevenue());
        assertEquals("last_30_days", response.period());
        assertTrue(response.dailyRevenue().isEmpty());
    }

    @Test
    void revenueUsesDefaultThirtyDayCutoff() {
        dashboardService.revenue(30);
        ArgumentCaptor<OffsetDateTime> cutoff = ArgumentCaptor.forClass(OffsetDateTime.class);
        verify(orderRepository).sumTotalAmountByStatusSince(eq(OrderStatus.completed), cutoff.capture());
        assertCutoffDays(cutoff.getValue(), 30);
    }

    @Test
    void revenueDaysFilterChangesCutoff() {
        dashboardService.revenue(7);
        ArgumentCaptor<OffsetDateTime> cutoff = ArgumentCaptor.forClass(OffsetDateTime.class);
        verify(orderRepository).sumTotalAmountByStatusSince(eq(OrderStatus.completed), cutoff.capture());
        assertCutoffDays(cutoff.getValue(), 7);
        DashboardRevenueResponse response = dashboardService.revenue(1);
        assertEquals("last_1_days", response.period());
    }

    @Test
    void expensesFillAllCategoryAndTypeKeysWhenEmpty() {
        DashboardExpenseBreakdownResponse response = dashboardService.expenses(30);
        assertEquals(ZERO, response.totalExpenses());
        assertEquals(ZERO, response.byCategory().get("inventory"));
        assertEquals(ZERO, response.byCategory().get("operations"));
        assertEquals(ZERO, response.byCategory().get("marketing"));
        assertEquals(3, response.byCategory().size());
        assertEquals(ZERO, response.byType().get("one_time"));
        assertEquals(ZERO, response.byType().get("recurring"));
        assertEquals(2, response.byType().size());
        assertTrue(response.monthlyExpenses().isEmpty());
    }

    @Test
    void expensesAggregateByCategoryTypeAndMonth() {
        when(expenseRepository.sumAmountSince(any())).thenReturn(new BigDecimal("80.00"));
        when(expenseRepository.sumAmountByCategorySince(any())).thenReturn(rows(
                new Object[]{ExpenseCategory.OPERATIONS, new BigDecimal("50.00")},
                new Object[]{ExpenseCategory.MARKETING, new BigDecimal("30.00")}
        ));
        when(expenseRepository.sumAmountByTypeSince(any())).thenReturn(rows(
                new Object[]{ExpenseType.RECURRING, new BigDecimal("50.00")},
                new Object[]{ExpenseType.ONE_TIME, new BigDecimal("30.00")}
        ));
        when(expenseRepository.sumAmountByMonthSince(any())).thenReturn(rows(
                new Object[]{2026.0, 8.0, new BigDecimal("80.00")}
        ));

        DashboardExpenseBreakdownResponse response = dashboardService.expenses(14);

        assertEquals(new BigDecimal("80.00"), response.totalExpenses());
        assertEquals(ZERO, response.byCategory().get("inventory"));
        assertEquals(new BigDecimal("50.00"), response.byCategory().get("operations"));
        assertEquals(new BigDecimal("30.00"), response.byCategory().get("marketing"));
        assertEquals(new BigDecimal("30.00"), response.byType().get("one_time"));
        assertEquals(new BigDecimal("50.00"), response.byType().get("recurring"));
        assertEquals(1, response.monthlyExpenses().size());
        assertEquals("2026-08", response.monthlyExpenses().getFirst().month());
        assertEquals(new BigDecimal("80.00"), response.monthlyExpenses().getFirst().amount());
        ArgumentCaptor<OffsetDateTime> cutoff = ArgumentCaptor.forClass(OffsetDateTime.class);
        verify(expenseRepository).sumAmountSince(cutoff.capture());
        assertCutoffDays(cutoff.getValue(), 14);
    }

    @Test
    void profitIsRevenueMinusExpensesAndZeroMarginWhenNoRevenue() {
        DashboardProfitResponse empty = dashboardService.profit(30);
        assertEquals(ZERO, empty.totalRevenue());
        assertEquals(ZERO, empty.totalExpenses());
        assertEquals(ZERO, empty.netProfit());
        assertEquals(ZERO, empty.profitMargin());
        assertTrue(empty.profitByProduct().isEmpty());

        when(orderRepository.sumTotalAmountByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(new BigDecimal("200.00"));
        when(expenseRepository.sumAmountSince(any())).thenReturn(new BigDecimal("50.00"));

        DashboardProfitResponse response = dashboardService.profit(30);
        assertEquals(new BigDecimal("200.00"), response.totalRevenue());
        assertEquals(new BigDecimal("50.00"), response.totalExpenses());
        assertEquals(new BigDecimal("150.00"), response.netProfit());
        assertEquals(new BigDecimal("75.0000000000"), response.profitMargin());
        verify(orderRepository, never()).sumTotalAmountByStatusSince(eq(OrderStatus.pending), any());
    }

    @Test
    void profitGroupsByProductUsingCompletedSalesAndProductExpenses() {
        when(orderRepository.sumTotalAmountByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(new BigDecimal("100.00"));
        when(expenseRepository.sumAmountSince(any())).thenReturn(new BigDecimal("20.00"));
        when(orderItemRepository.aggregateProductSales(eq(OrderStatus.completed), any()))
                .thenReturn(rows(new Object[]{10, "Widget", 4L, new BigDecimal("100.00")}));
        when(expenseRepository.sumAmountByProductSince(any())).thenReturn(rows(
                new Object[]{10, new BigDecimal("20.00")},
                new Object[]{99, new BigDecimal("5.00")}
        ));

        DashboardProfitResponse response = dashboardService.profit(30);
        assertEquals(1, response.profitByProduct().size());
        DashboardProfitResponse.ProductProfit row = response.profitByProduct().getFirst();
        assertEquals(10, row.productId());
        assertEquals("Widget", row.productName());
        assertEquals(new BigDecimal("100.00"), row.revenue());
        assertEquals(new BigDecimal("20.00"), row.expenses());
        assertEquals(new BigDecimal("80.00"), row.profit());
        assertEquals(new BigDecimal("80.0000000000"), row.margin());
    }

    @Test
    void stockStatusCountsLowOutAndInventoryValue() {
        Product out = product(1, "Gone", 0, 5, "9.00");
        Product low = product(2, "Low", 2, 5, "4.00");
        when(productRepository.count()).thenReturn(3L);
        when(productRepository.sumInventoryValue()).thenReturn(new BigDecimal("17.00"));
        when(productRepository.findOutOfStock()).thenReturn(List.of(out));
        when(productRepository.findLowStock()).thenReturn(List.of(low));

        DashboardStockStatusResponse response = dashboardService.stockStatus();
        assertEquals(3, response.totalProducts());
        assertEquals(new BigDecimal("17.00"), response.stockValue());
        assertEquals(1, response.outOfStockProducts().size());
        assertEquals(1, response.outOfStockProducts().getFirst().productId());
        assertEquals("Gone", response.outOfStockProducts().getFirst().name());
        assertEquals(0, response.outOfStockProducts().getFirst().stockQuantity());
        assertEquals(5, response.outOfStockProducts().getFirst().threshold());
        assertEquals(1, response.lowStockProducts().size());
        assertEquals(2, response.lowStockProducts().getFirst().productId());
        assertEquals(2, response.lowStockProducts().getFirst().stockQuantity());
    }

    @Test
    void stockStatusEmptyCatalog() {
        DashboardStockStatusResponse response = dashboardService.stockStatus();
        assertEquals(0, response.totalProducts());
        assertEquals(ZERO, response.stockValue());
        assertTrue(response.lowStockProducts().isEmpty());
        assertTrue(response.outOfStockProducts().isEmpty());
    }

    @Test
    void salesAggregatesCompletedOrdersProductsAndDates() {
        when(orderRepository.countByStatusSince(eq(OrderStatus.completed), any())).thenReturn(2L);
        when(orderRepository.sumTotalAmountByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(new BigDecimal("40.00"));
        when(orderItemRepository.aggregateProductSales(eq(OrderStatus.completed), any()))
                .thenReturn(rows(new Object[]{10, "Widget", 8L, new BigDecimal("40.00")}));
        when(orderRepository.dailySalesByStatusSince(eq(OrderStatus.completed), any()))
                .thenReturn(rows(new Object[]{Date.valueOf("2026-08-10"), 2L, new BigDecimal("40.00")}));

        DashboardSalesResponse response = dashboardService.sales(30);
        assertEquals(2, response.totalSales());
        assertEquals(new BigDecimal("40.00"), response.totalRevenue());
        assertEquals(1, response.salesByProduct().size());
        assertEquals(10, response.salesByProduct().getFirst().productId());
        assertEquals("Widget", response.salesByProduct().getFirst().name());
        assertEquals(8, response.salesByProduct().getFirst().quantitySold());
        assertEquals(new BigDecimal("40.00"), response.salesByProduct().getFirst().revenue());
        assertEquals(1, response.salesOverTime().size());
        assertEquals("2026-08-10", response.salesOverTime().getFirst().date());
        assertEquals(2, response.salesOverTime().getFirst().orders());
        verify(orderRepository, never()).countByStatusSince(eq(OrderStatus.cancelled), any());
    }

    @Test
    void salesDateFilterUsesRequestedDays() {
        dashboardService.sales(365);
        ArgumentCaptor<OffsetDateTime> cutoff = ArgumentCaptor.forClass(OffsetDateTime.class);
        verify(orderRepository).countByStatusSince(eq(OrderStatus.completed), cutoff.capture());
        assertCutoffDays(cutoff.getValue(), 365);
    }

    private static List<Object[]> rows(Object[]... rows) {
        return List.of(rows);
    }

    private static Product product(int id, String name, int qty, int threshold, String price) {
        Product product = new Product();
        product.setId(id);
        product.setName(name);
        product.setStockQuantity(qty);
        product.setStockThreshold(threshold);
        product.setPrice(new BigDecimal(price));
        return product;
    }

    private static void assertCutoffDays(OffsetDateTime cutoff, int days) {
        OffsetDateTime expected = OffsetDateTime.now(ZoneOffset.UTC).minusDays(days);
        long seconds = Math.abs(ChronoUnit.SECONDS.between(cutoff, expected));
        assertTrue(seconds < 5, "cutoff should be now-UTC minus " + days + " days, delta=" + seconds);
    }
}
