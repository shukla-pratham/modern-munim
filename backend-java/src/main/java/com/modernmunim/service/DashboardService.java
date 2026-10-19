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
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Read-only dashboard aggregations matching FastAPI {@code dashboard_service.py}.
 * Totals are computed in the database — never via capped list APIs.
 */
@Service
@RequiredArgsConstructor
public class DashboardService {

    private static final BigDecimal ZERO = new BigDecimal("0.00");
    private static final BigDecimal HUNDRED = new BigDecimal("100");
    private static final int MARGIN_SCALE = 10;

    private final OrderRepository orderRepository;
    private final OrderItemRepository orderItemRepository;
    private final ExpenseRepository expenseRepository;
    private final ProductRepository productRepository;

    @Transactional(readOnly = true)
    public DashboardRevenueResponse revenue(int days) {
        OffsetDateTime cutoff = cutoff(days);
        BigDecimal total = money(orderRepository.sumTotalAmountByStatusSince(OrderStatus.completed, cutoff));
        List<DashboardRevenueResponse.DailyRevenue> daily = new ArrayList<>();
        for (Object[] row : orderRepository.dailyRevenueByStatusSince(OrderStatus.completed, cutoff)) {
            daily.add(new DashboardRevenueResponse.DailyRevenue(toDateString(row[0]), money(row[1])));
        }
        return new DashboardRevenueResponse(total, period(days), daily);
    }

    @Transactional(readOnly = true)
    public DashboardExpenseBreakdownResponse expenses(int days) {
        OffsetDateTime cutoff = cutoff(days);
        BigDecimal total = money(expenseRepository.sumAmountSince(cutoff));

        Map<String, BigDecimal> byCategory = new LinkedHashMap<>();
        for (ExpenseCategory category : ExpenseCategory.values()) {
            byCategory.put(category.apiValue(), ZERO);
        }
        for (Object[] row : expenseRepository.sumAmountByCategorySince(cutoff)) {
            ExpenseCategory category = (ExpenseCategory) row[0];
            byCategory.put(category.apiValue(), money(row[1]));
        }

        Map<String, BigDecimal> byType = new LinkedHashMap<>();
        for (ExpenseType type : ExpenseType.values()) {
            byType.put(type.apiValue(), ZERO);
        }
        for (Object[] row : expenseRepository.sumAmountByTypeSince(cutoff)) {
            ExpenseType type = (ExpenseType) row[0];
            byType.put(type.apiValue(), money(row[1]));
        }

        List<DashboardExpenseBreakdownResponse.MonthlyAmount> monthly = new ArrayList<>();
        for (Object[] row : expenseRepository.sumAmountByMonthSince(cutoff)) {
            int year = toInt(row[0]);
            int month = toInt(row[1]);
            monthly.add(new DashboardExpenseBreakdownResponse.MonthlyAmount(
                    String.format("%d-%02d", year, month), money(row[2])));
        }

        return new DashboardExpenseBreakdownResponse(total, byCategory, byType, monthly);
    }

    @Transactional(readOnly = true)
    public DashboardProfitResponse profit(int days) {
        OffsetDateTime cutoff = cutoff(days);
        BigDecimal totalRevenue = money(orderRepository.sumTotalAmountByStatusSince(OrderStatus.completed, cutoff));
        BigDecimal totalExpenses = money(expenseRepository.sumAmountSince(cutoff));
        BigDecimal netProfit = totalRevenue.subtract(totalExpenses);
        BigDecimal profitMargin = margin(netProfit, totalRevenue);

        Map<Integer, BigDecimal> expensesByProduct = new HashMap<>();
        for (Object[] row : expenseRepository.sumAmountByProductSince(cutoff)) {
            if (row[0] != null) {
                expensesByProduct.put((Integer) row[0], money(row[1]));
            }
        }

        List<DashboardProfitResponse.ProductProfit> byProduct = new ArrayList<>();
        for (Object[] row : orderItemRepository.aggregateProductSales(OrderStatus.completed, cutoff)) {
            Integer productId = (Integer) row[0];
            String name = (String) row[1];
            BigDecimal productRevenue = money(row[3]);
            BigDecimal productExpenses = expensesByProduct.getOrDefault(productId, ZERO);
            BigDecimal productProfit = productRevenue.subtract(productExpenses);
            byProduct.add(new DashboardProfitResponse.ProductProfit(
                    productId,
                    name,
                    productRevenue,
                    productExpenses,
                    productProfit,
                    margin(productProfit, productRevenue)
            ));
        }

        return new DashboardProfitResponse(totalRevenue, totalExpenses, netProfit, profitMargin, byProduct);
    }

    @Transactional(readOnly = true)
    public DashboardStockStatusResponse stockStatus() {
        int totalProducts = Math.toIntExact(productRepository.count());
        BigDecimal stockValue = money(productRepository.sumInventoryValue());
        List<DashboardStockStatusResponse.StockProduct> outOfStock = productRepository.findOutOfStock()
                .stream()
                .map(DashboardService::toStockProduct)
                .toList();
        List<DashboardStockStatusResponse.StockProduct> lowStock = productRepository.findLowStock()
                .stream()
                .map(DashboardService::toStockProduct)
                .toList();
        return new DashboardStockStatusResponse(totalProducts, lowStock, outOfStock, stockValue);
    }

    @Transactional(readOnly = true)
    public DashboardSalesResponse sales(int days) {
        OffsetDateTime cutoff = cutoff(days);
        int totalSales = Math.toIntExact(orderRepository.countByStatusSince(OrderStatus.completed, cutoff));
        BigDecimal totalRevenue = money(orderRepository.sumTotalAmountByStatusSince(OrderStatus.completed, cutoff));

        List<DashboardSalesResponse.ProductSales> byProduct = new ArrayList<>();
        for (Object[] row : orderItemRepository.aggregateProductSales(OrderStatus.completed, cutoff)) {
            byProduct.add(new DashboardSalesResponse.ProductSales(
                    (Integer) row[0],
                    (String) row[1],
                    toInt(row[2]),
                    money(row[3])
            ));
        }

        List<DashboardSalesResponse.SalesOverTime> overTime = new ArrayList<>();
        for (Object[] row : orderRepository.dailySalesByStatusSince(OrderStatus.completed, cutoff)) {
            overTime.add(new DashboardSalesResponse.SalesOverTime(
                    toDateString(row[0]),
                    toInt(row[1]),
                    money(row[2])
            ));
        }

        return new DashboardSalesResponse(totalSales, totalRevenue, byProduct, overTime);
    }

    static OffsetDateTime cutoff(int days) {
        return OffsetDateTime.now(ZoneOffset.UTC).minusDays(days);
    }

    private static String period(int days) {
        return "last_" + days + "_days";
    }

    private static DashboardStockStatusResponse.StockProduct toStockProduct(Product product) {
        return new DashboardStockStatusResponse.StockProduct(
                product.getId(),
                product.getName(),
                product.getStockQuantity(),
                product.getStockThreshold()
        );
    }

    private static BigDecimal margin(BigDecimal net, BigDecimal revenue) {
        if (revenue.compareTo(BigDecimal.ZERO) <= 0) {
            return ZERO;
        }
        return net.multiply(HUNDRED).divide(revenue, MARGIN_SCALE, RoundingMode.HALF_UP);
    }

    private static BigDecimal money(Object value) {
        if (value == null) {
            return ZERO;
        }
        if (value instanceof BigDecimal bd) {
            return bd;
        }
        if (value instanceof Number n) {
            return new BigDecimal(n.toString());
        }
        return new BigDecimal(value.toString());
    }

    private static int toInt(Object value) {
        if (value == null) {
            return 0;
        }
        if (value instanceof Number n) {
            return n.intValue();
        }
        return Integer.parseInt(value.toString());
    }

    private static String toDateString(Object value) {
        return switch (value) {
            case null -> throw new IllegalStateException("grouped date was null");
            case LocalDate d -> d.toString();
            case java.sql.Date d -> d.toLocalDate().toString();
            case java.util.Date d -> d.toInstant().atZone(ZoneOffset.UTC).toLocalDate().toString();
            case OffsetDateTime odt -> odt.toLocalDate().toString();
            default -> value.toString();
        };
    }
}
