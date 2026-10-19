package com.modernmunim.service;

import com.modernmunim.dto.PurchaseOrderCreateRequest;
import com.modernmunim.dto.PurchaseOrderItemCreateRequest;
import com.modernmunim.dto.PurchaseOrderResponse;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.PurchaseOrder;
import com.modernmunim.entity.PurchaseOrderItem;
import com.modernmunim.entity.PurchaseOrderStatuses;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.TransactionType;
import com.modernmunim.entity.Vendor;
import com.modernmunim.entity.VendorProduct;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.PurchaseOrderRepository;
import com.modernmunim.repository.StockTransactionRepository;
import com.modernmunim.repository.VendorProductRepository;
import com.modernmunim.repository.VendorRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.List;

/**
 * Create/list match FastAPI {@code create_purchase_order} / {@code list_purchase_orders}.
 * Deliver is the Spring HTTP receiving path (FastAPI has service logic but no HTTP route).
 */
@Service
@RequiredArgsConstructor
public class PurchaseOrderService {

    private static final Logger log = LoggerFactory.getLogger(PurchaseOrderService.class);
    private static final DateTimeFormatter PO_DATE = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final int LIST_LIMIT = 100;

    private final PurchaseOrderRepository purchaseOrderRepository;
    private final ProductRepository productRepository;
    private final StockTransactionRepository stockTransactionRepository;
    private final VendorRepository vendorRepository;
    private final VendorProductRepository vendorProductRepository;

    @Transactional
    public PurchaseOrderResponse create(PurchaseOrderCreateRequest request) {
        List<PurchaseOrderItemCreateRequest> items = request.items();
        if (items == null || items.isEmpty()) {
            throw DomainExceptions.purchaseOrderItemsRequired();
        }

        Vendor vendor = vendorRepository.findByIdForUpdate(request.vendorId())
                .orElseThrow(() -> DomainExceptions.validation("Vendor " + request.vendorId() + " not found"));
        if (!Boolean.TRUE.equals(vendor.getIsActive())) {
            throw DomainExceptions.validation("Vendor " + request.vendorId() + " is not active");
        }

        BigDecimal totalCost = BigDecimal.ZERO;
        for (PurchaseOrderItemCreateRequest item : items) {
            productRepository.findByIdForUpdate(item.productId())
                    .orElseThrow(() -> DomainExceptions.validation("Product " + item.productId() + " not found"));

            VendorProduct vendorProduct = vendorProductRepository
                    .findByVendorIdAndProductId(request.vendorId(), item.productId())
                    .orElseThrow(() -> DomainExceptions.validation(
                            "Vendor " + request.vendorId() + " does not supply product " + item.productId()));

            int minQty = vendorProduct.getMinOrderQty() != null ? vendorProduct.getMinOrderQty() : 1;
            if (item.quantity() < minQty) {
                throw DomainExceptions.validation(
                        "Quantity " + item.quantity() + " below minimum order quantity " + minQty);
            }
            totalCost = totalCost.add(BigDecimal.valueOf(item.quantity()).multiply(item.unitCost()));
        }

        Integer maxId = purchaseOrderRepository.findMaxId();
        // FastAPI: `func.max(...).scalar() or 0 + 1` → max id if present else 1
        int seq = maxId == null ? 1 : maxId;
        String poNumber = "PO-" + OffsetDateTime.now().format(PO_DATE) + "-" + request.vendorId() + "-" + seq;

        PurchaseOrder po = new PurchaseOrder();
        po.setVendorId(request.vendorId());
        po.setVendor(vendor);
        po.setPoNumber(poNumber);
        po.setStatus(PurchaseOrderStatuses.CREATED);
        po.setTotalCost(totalCost);
        po.setPromisedDeliveryDate(request.promisedDeliveryDate());
        po.setOrderDate(OffsetDateTime.now());

        for (PurchaseOrderItemCreateRequest item : items) {
            PurchaseOrderItem row = new PurchaseOrderItem();
            row.setPurchaseOrder(po);
            row.setProductId(item.productId());
            row.setQuantity(item.quantity());
            row.setUnitCost(item.unitCost());
            row.setTotalCost(BigDecimal.valueOf(item.quantity()).multiply(item.unitCost()));
            po.getItems().add(row);
        }

        PurchaseOrder saved = purchaseOrderRepository.save(po);
        log.info("Created purchase order {} for vendor {}", saved.getPoNumber(), request.vendorId());
        return reloadResponse(saved.getId());
    }

    @Transactional(readOnly = true)
    public List<PurchaseOrderResponse> list(Integer vendorId) {
        var page = PageRequest.of(0, LIST_LIMIT);
        List<PurchaseOrder> orders = vendorId == null
                ? purchaseOrderRepository.findRecent(page)
                : purchaseOrderRepository.findRecentByVendor(vendorId, page);
        return orders.stream().map(DtoMapper::toPurchaseOrderResponse).toList();
    }

    @Transactional
    public PurchaseOrderResponse deliver(Integer purchaseOrderId, OffsetDateTime actualDeliveryDate) {
        PurchaseOrder po = purchaseOrderRepository.findByIdForUpdate(purchaseOrderId)
                .orElseThrow(() -> DomainExceptions.purchaseOrderNotFound(purchaseOrderId));

        if (PurchaseOrderStatuses.DELIVERED.equals(po.getStatus())) {
            return reloadResponse(po.getId());
        }

        OffsetDateTime deliveryAt = actualDeliveryDate != null ? actualDeliveryDate : OffsetDateTime.now();
        Integer delayDays = computeDelayDays(po.getPromisedDeliveryDate(), deliveryAt);

        List<PurchaseOrderItem> items = po.getItems();
        if (items == null || items.isEmpty()) {
            // Still mark delivered (empty PO) — match "receive" semantics; no stock/ledger.
            applyDeliveredState(po, deliveryAt, delayDays);
            return reloadResponse(purchaseOrderRepository.save(po).getId());
        }

        String reason = "Purchase order " + po.getPoNumber() + " delivered";

        for (PurchaseOrderItem item : items) {
            Product product = productRepository.findByIdForUpdate(item.getProductId())
                    .orElseThrow(() -> DomainExceptions.productNotFound(item.getProductId()));

            int qty = item.getQuantity();
            product.setStockQuantity(product.getStockQuantity() + qty);

            StockTransaction tx = new StockTransaction();
            tx.setProductId(product.getId());
            tx.setProduct(product);
            tx.setQuantityChange(qty);
            tx.setTransactionType(TransactionType.in);
            tx.setReason(reason);
            stockTransactionRepository.save(tx);
        }

        applyDeliveredState(po, deliveryAt, delayDays);
        purchaseOrderRepository.save(po);

        log.info("Delivered purchase order {} (delay_days={})", po.getPoNumber(), delayDays);
        return reloadResponse(po.getId());
    }

    /**
     * FastAPI rule: if promised date exists,
     * {@code delay = (actual - promised).days}; {@code delay_days = delay if delay > 0 else 0}.
     * Uses whole 24h periods between the instants (same as Python timedelta.days),
     * not calendar local-dates (which break when timestamptz is normalized to UTC).
     * Early deliveries are recorded as 0, not negative.
     */
    static Integer computeDelayDays(OffsetDateTime promised, OffsetDateTime actual) {
        if (promised == null || actual == null) {
            return null;
        }
        long delay = ChronoUnit.DAYS.between(promised, actual);
        return delay > 0 ? (int) delay : 0;
    }

    private static void applyDeliveredState(PurchaseOrder po, OffsetDateTime deliveryAt, Integer delayDays) {
        po.setStatus(PurchaseOrderStatuses.DELIVERED);
        po.setActualDeliveryDate(deliveryAt);
        po.setDelayDays(delayDays);
    }

    private PurchaseOrderResponse reloadResponse(Integer id) {
        PurchaseOrder detailed = purchaseOrderRepository.findByIdWithDetails(id)
                .orElseThrow(() -> DomainExceptions.purchaseOrderNotFound(id));
        return DtoMapper.toPurchaseOrderResponse(detailed);
    }
}
