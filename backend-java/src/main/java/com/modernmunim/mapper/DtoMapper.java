package com.modernmunim.mapper;

import com.modernmunim.dto.ExpenseResponse;
import com.modernmunim.dto.OrderItemResponse;
import com.modernmunim.dto.OrderResponse;
import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.PurchaseOrderItemResponse;
import com.modernmunim.dto.PurchaseOrderResponse;
import com.modernmunim.dto.StockTransactionResponse;
import com.modernmunim.dto.UserResponse;
import com.modernmunim.dto.VendorCreateResponse;
import com.modernmunim.dto.VendorPerformanceResponse;
import com.modernmunim.dto.VendorProductResponse;
import com.modernmunim.entity.Expense;
import com.modernmunim.entity.Order;
import com.modernmunim.entity.OrderItem;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.PurchaseOrder;
import com.modernmunim.entity.PurchaseOrderItem;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.User;
import com.modernmunim.entity.Vendor;
import com.modernmunim.entity.VendorPerformanceMetric;
import com.modernmunim.entity.VendorProduct;

import java.math.BigDecimal;
import java.util.List;

public final class DtoMapper {

    private DtoMapper() {}

    public static ProductResponse toProductResponse(Product p) {
        return new ProductResponse(
                p.getId(),
                p.getName(),
                p.getDescription(),
                p.getPrice(),
                p.getStockQuantity(),
                p.getStockThreshold(),
                p.getCreatedAt(),
                p.getUpdatedAt()
        );
    }

    public static StockTransactionResponse toStockTransactionResponse(StockTransaction t) {
        String productName = t.getProduct() != null ? t.getProduct().getName() : null;
        return new StockTransactionResponse(
                t.getId(),
                t.getProductId(),
                productName,
                t.getQuantityChange(),
                t.getTransactionType() != null ? t.getTransactionType().name() : null,
                t.getReason(),
                t.getCreatedAt()
        );
    }

    public static UserResponse toUserResponse(User u) {
        return new UserResponse(
                u.getId(),
                u.getEmail(),
                u.getRole() != null ? u.getRole().name() : null,
                u.getCreatedAt()
        );
    }

    public static OrderItemResponse toOrderItemResponse(OrderItem item) {
        String productName = item.getProduct() != null ? item.getProduct().getName() : null;
        return new OrderItemResponse(
                item.getId(),
                item.getProductId(),
                productName,
                item.getQuantity(),
                item.getPriceAtPurchase()
        );
    }

    public static OrderResponse toOrderResponse(Order order) {
        List<OrderItemResponse> items = order.getItems() == null
                ? List.of()
                : order.getItems().stream().map(DtoMapper::toOrderItemResponse).toList();
        return new OrderResponse(
                order.getId(),
                order.getUserId(),
                order.getTotalAmount(),
                order.getStatus() != null ? order.getStatus().name() : null,
                order.getCreatedAt(),
                items
        );
    }

    public static PurchaseOrderItemResponse toPurchaseOrderItemResponse(PurchaseOrderItem item) {
        String productName = item.getProduct() != null
                ? item.getProduct().getName()
                : ("Product #" + item.getProductId());
        return new PurchaseOrderItemResponse(
                item.getProductId(),
                productName,
                item.getQuantity(),
                item.getUnitCost(),
                item.getTotalCost()
        );
    }

    public static ExpenseResponse toExpenseResponse(Expense e) {
        String productName = e.getProduct() != null ? e.getProduct().getName() : null;
        return new ExpenseResponse(
                e.getId(),
                e.getCategory() != null ? e.getCategory().apiValue() : null,
                e.getDescription(),
                e.getAmount(),
                e.getExpenseType() != null ? e.getExpenseType().apiValue() : null,
                e.getProductId(),
                productName,
                e.getCreatedAt()
        );
    }

    public static VendorCreateResponse toVendorCreateResponse(Vendor v) {
        return new VendorCreateResponse(
                v.getId(),
                v.getName(),
                v.getIsActive(),
                v.getAvgLeadTimeDays(),
                v.getReliabilityScore(),
                v.getCostScore(),
                v.getOverallScore()
        );
    }

    public static VendorProductResponse toVendorProductResponse(VendorProduct vp) {
        String productName = vp.getProduct() != null && vp.getProduct().getName() != null
                ? vp.getProduct().getName()
                : ("Product " + vp.getProductId());
        BigDecimal unitCost = vp.getUnitCost() != null ? vp.getUnitCost() : BigDecimal.ZERO;
        Integer minQty = vp.getMinOrderQty() != null ? vp.getMinOrderQty() : 1;
        return new VendorProductResponse(
                vp.getId(),
                vp.getProductId(),
                productName,
                unitCost,
                minQty,
                vp.getLeadTimeDays()
        );
    }

    public static VendorPerformanceResponse toVendorPerformanceResponse(Vendor vendor, VendorPerformanceMetric metric) {
        return new VendorPerformanceResponse(
                vendor.getId(),
                vendor.getName(),
                metric.getMetricDate(),
                metric.getAvgLeadTime(),
                metric.getOnTimeDeliveryRate(),
                metric.getFulfillmentRate(),
                metric.getAvgUnitCost(),
                metric.getPriceVariance(),
                metric.getDelayDaysAvg()
        );
    }

    public static PurchaseOrderResponse toPurchaseOrderResponse(PurchaseOrder po) {
        String vendorName = po.getVendor() != null ? po.getVendor().getName() : "";
        List<PurchaseOrderItemResponse> items = po.getItems() == null
                ? List.of()
                : po.getItems().stream().map(DtoMapper::toPurchaseOrderItemResponse).toList();
        return new PurchaseOrderResponse(
                po.getId(),
                po.getVendorId(),
                vendorName,
                po.getPoNumber(),
                po.getStatus(),
                po.getTotalCost(),
                po.getOrderDate(),
                po.getPromisedDeliveryDate(),
                po.getActualDeliveryDate(),
                po.getDelayDays(),
                items
        );
    }
}
