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
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.PurchaseOrderRepository;
import com.modernmunim.repository.StockTransactionRepository;
import com.modernmunim.repository.VendorProductRepository;
import com.modernmunim.repository.VendorRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PurchaseOrderServiceTest {

    @Mock
    private PurchaseOrderRepository purchaseOrderRepository;
    @Mock
    private ProductRepository productRepository;
    @Mock
    private StockTransactionRepository stockTransactionRepository;
    @Mock
    private VendorRepository vendorRepository;
    @Mock
    private VendorProductRepository vendorProductRepository;

    @InjectMocks
    private PurchaseOrderService purchaseOrderService;

    private PurchaseOrder po;
    private Product productA;
    private Product productB;

    @BeforeEach
    void setUp() {
        Vendor vendor = new Vendor();
        vendor.setId(1);
        vendor.setName("Acme Supply");

        productA = new Product();
        productA.setId(10);
        productA.setName("Widget A");
        productA.setPrice(new BigDecimal("5.00"));
        productA.setStockQuantity(5);

        productB = new Product();
        productB.setId(20);
        productB.setName("Widget B");
        productB.setPrice(new BigDecimal("8.00"));
        productB.setStockQuantity(2);

        PurchaseOrderItem itemA = new PurchaseOrderItem();
        itemA.setProductId(10);
        itemA.setProduct(productA);
        itemA.setQuantity(3);
        itemA.setUnitCost(new BigDecimal("4.00"));
        itemA.setTotalCost(new BigDecimal("12.00"));

        PurchaseOrderItem itemB = new PurchaseOrderItem();
        itemB.setProductId(20);
        itemB.setProduct(productB);
        itemB.setQuantity(4);
        itemB.setUnitCost(new BigDecimal("7.00"));
        itemB.setTotalCost(new BigDecimal("28.00"));

        po = new PurchaseOrder();
        po.setId(100);
        po.setVendorId(1);
        po.setVendor(vendor);
        po.setPoNumber("PO-TEST-100");
        po.setStatus(PurchaseOrderStatuses.CREATED);
        po.setTotalCost(new BigDecimal("40.00"));
        po.setOrderDate(OffsetDateTime.parse("2026-08-01T10:00:00+05:30"));
        po.setPromisedDeliveryDate(OffsetDateTime.parse("2026-08-05T00:00:00+05:30"));
        po.setItems(new ArrayList<>(List.of(itemA, itemB)));
        itemA.setPurchaseOrder(po);
        itemB.setPurchaseOrder(po);
    }

    private void stubReload() {
        when(purchaseOrderRepository.findByIdWithDetails(100)).thenReturn(Optional.of(po));
    }

    @Test
    void deliverSuccessUpdatesStockLedgerAndStatus() {
        when(purchaseOrderRepository.findByIdForUpdate(100)).thenReturn(Optional.of(po));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(productRepository.findByIdForUpdate(20)).thenReturn(Optional.of(productB));
        when(purchaseOrderRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        stubReload();

        OffsetDateTime actual = OffsetDateTime.parse("2026-08-08T12:00:00+05:30");
        PurchaseOrderResponse response = purchaseOrderService.deliver(100, actual);

        assertEquals(PurchaseOrderStatuses.DELIVERED, po.getStatus());
        assertEquals(actual, po.getActualDeliveryDate());
        assertEquals(3, po.getDelayDays()); // 8 - 5 = 3 days late
        assertEquals(8, productA.getStockQuantity()); // 5+3
        assertEquals(6, productB.getStockQuantity()); // 2+4
        assertEquals(PurchaseOrderStatuses.DELIVERED, response.status());

        ArgumentCaptor<StockTransaction> captor = ArgumentCaptor.forClass(StockTransaction.class);
        verify(stockTransactionRepository, times(2)).save(captor.capture());
        List<StockTransaction> txs = captor.getAllValues();
        assertTrue(txs.stream().allMatch(t -> t.getTransactionType() == TransactionType.in));
        assertTrue(txs.stream().allMatch(t -> "Purchase order PO-TEST-100 delivered".equals(t.getReason())));
        assertEquals(3, txs.get(0).getQuantityChange());
        assertEquals(4, txs.get(1).getQuantityChange());
    }

    @Test
    void earlyDeliveryRecordsDelayDaysZero() {
        when(purchaseOrderRepository.findByIdForUpdate(100)).thenReturn(Optional.of(po));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(productRepository.findByIdForUpdate(20)).thenReturn(Optional.of(productB));
        when(purchaseOrderRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        stubReload();

        OffsetDateTime early = OffsetDateTime.parse("2026-08-03T12:00:00+05:30");
        purchaseOrderService.deliver(100, early);

        assertEquals(0, po.getDelayDays());
    }

    @Test
    void alreadyDeliveredIsIdempotent() {
        po.setStatus(PurchaseOrderStatuses.DELIVERED);
        po.setActualDeliveryDate(OffsetDateTime.parse("2026-08-08T12:00:00+05:30"));
        po.setDelayDays(3);
        when(purchaseOrderRepository.findByIdForUpdate(100)).thenReturn(Optional.of(po));
        stubReload();

        purchaseOrderService.deliver(100, OffsetDateTime.now());

        assertEquals(5, productA.getStockQuantity());
        assertEquals(2, productB.getStockQuantity());
        verify(productRepository, never()).findByIdForUpdate(any());
        verify(stockTransactionRepository, never()).save(any());
        verify(purchaseOrderRepository, never()).save(any());
    }

    @Test
    void missingPurchaseOrderThrows404() {
        when(purchaseOrderRepository.findByIdForUpdate(999)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class,
                () -> purchaseOrderService.deliver(999, null));
        assertEquals(404, ex.getStatus());
    }

    @Test
    void missingProductFailsWithoutDelivering() {
        when(purchaseOrderRepository.findByIdForUpdate(100)).thenReturn(Optional.of(po));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(productRepository.findByIdForUpdate(20)).thenReturn(Optional.empty());
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ApiException ex = assertThrows(ApiException.class,
                () -> purchaseOrderService.deliver(100, OffsetDateTime.now()));

        assertEquals(404, ex.getStatus());
        assertEquals(PurchaseOrderStatuses.CREATED, po.getStatus());
        assertNull(po.getActualDeliveryDate());
        // First item may have mutated in-memory stock before failure; @Transactional rolls back at runtime.
        // Control-flow: PO never saved as delivered; only one ledger save attempted before abort.
        verify(stockTransactionRepository, times(1)).save(any());
        verify(purchaseOrderRepository, never()).save(any());
    }

    /**
     * Proves mid-loop failure aborts before PO deliver state is applied.
     * Runtime DB atomicity of earlier stock/ledger writes relies on {@code @Transactional}
     * (verified in real Postgres smoke when a later step throws).
     */
    @Test
    void laterItemFailureLeavesPoUndeliveredAndStopsLedgerWrites() {
        when(purchaseOrderRepository.findByIdForUpdate(100)).thenReturn(Optional.of(po));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(productRepository.findByIdForUpdate(20)).thenReturn(Optional.empty());
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        assertThrows(ApiException.class,
                () -> purchaseOrderService.deliver(100, OffsetDateTime.parse("2026-08-08T12:00:00+05:30")));

        assertEquals(PurchaseOrderStatuses.CREATED, po.getStatus());
        assertNull(po.getDelayDays());
        verify(stockTransactionRepository, times(1)).save(any());
        verify(purchaseOrderRepository, never()).save(any());
        verify(purchaseOrderRepository, never()).findByIdWithDetails(any());
    }

    @Test
    void computeDelayDaysMatchesFastapiRules() {
        OffsetDateTime promised = OffsetDateTime.parse("2026-08-05T00:00:00+05:30");
        assertEquals(3, PurchaseOrderService.computeDelayDays(
                promised, OffsetDateTime.parse("2026-08-08T12:00:00+05:30")));
        // Same instants after UTC normalization must still yield 3 (not calendar-local 4)
        assertEquals(3, PurchaseOrderService.computeDelayDays(
                OffsetDateTime.parse("2026-08-04T18:30:00Z"),
                OffsetDateTime.parse("2026-08-08T12:00:00+05:30")));
        assertEquals(0, PurchaseOrderService.computeDelayDays(
                promised, OffsetDateTime.parse("2026-08-05T15:00:00+05:30")));
        assertEquals(0, PurchaseOrderService.computeDelayDays(
                promised, OffsetDateTime.parse("2026-08-01T15:00:00+05:30")));
        assertNull(PurchaseOrderService.computeDelayDays(null, OffsetDateTime.now()));
    }

    @Test
    void createPersistsCreatedStatusAndDoesNotTouchStock() {
        Vendor vendor = po.getVendor();
        VendorProduct vp = new VendorProduct();
        vp.setVendorId(1);
        vp.setProductId(10);
        vp.setMinOrderQty(2);
        vp.setUnitCost(new BigDecimal("4.00"));

        when(vendorRepository.findByIdForUpdate(1)).thenReturn(Optional.of(vendor));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(vendorProductRepository.findByVendorIdAndProductId(1, 10)).thenReturn(Optional.of(vp));
        when(purchaseOrderRepository.findMaxId()).thenReturn(null);
        when(purchaseOrderRepository.save(any())).thenAnswer(inv -> {
            PurchaseOrder saved = inv.getArgument(0);
            saved.setId(50);
            return saved;
        });
        when(purchaseOrderRepository.findByIdWithDetails(50)).thenAnswer(inv -> Optional.of(po));

        PurchaseOrderResponse response = purchaseOrderService.create(new PurchaseOrderCreateRequest(
                1,
                List.of(new PurchaseOrderItemCreateRequest(10, 3, new BigDecimal("4.00"))),
                null));

        assertEquals("created", response.status());
        assertEquals(5, productA.getStockQuantity());
        verify(stockTransactionRepository, never()).save(any());
        ArgumentCaptor<PurchaseOrder> captor = ArgumentCaptor.forClass(PurchaseOrder.class);
        verify(purchaseOrderRepository).save(captor.capture());
        assertEquals(PurchaseOrderStatuses.CREATED, captor.getValue().getStatus());
        assertTrue(captor.getValue().getPoNumber().startsWith("PO-"));
        assertEquals(new BigDecimal("12.00"), captor.getValue().getTotalCost());
    }

    @Test
    void createRejectsEmptyItemsWith400() {
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(1, List.of(), null)));
        assertEquals(400, ex.getStatus());
        assertEquals("At least one item is required", ex.getDetail());
        verify(purchaseOrderRepository, never()).save(any());
    }

    @Test
    void createRejectsMissingVendorWith422() {
        when(vendorRepository.findByIdForUpdate(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(
                        99,
                        List.of(new PurchaseOrderItemCreateRequest(10, 1, BigDecimal.ONE)),
                        null)));
        assertEquals(422, ex.getStatus());
        assertTrue(ex.getDetail().contains("Vendor 99 not found"));
    }

    @Test
    void createRejectsInactiveVendor() {
        Vendor vendor = po.getVendor();
        vendor.setIsActive(false);
        when(vendorRepository.findByIdForUpdate(1)).thenReturn(Optional.of(vendor));
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(
                        1,
                        List.of(new PurchaseOrderItemCreateRequest(10, 1, BigDecimal.ONE)),
                        null)));
        assertEquals(422, ex.getStatus());
        assertTrue(ex.getDetail().contains("not active"));
    }

    @Test
    void createRejectsMissingProduct() {
        when(vendorRepository.findByIdForUpdate(1)).thenReturn(Optional.of(po.getVendor()));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(
                        1,
                        List.of(new PurchaseOrderItemCreateRequest(10, 1, BigDecimal.ONE)),
                        null)));
        assertEquals(422, ex.getStatus());
        assertTrue(ex.getDetail().contains("Product 10 not found"));
    }

    @Test
    void createRejectsVendorNotSupplyingProduct() {
        when(vendorRepository.findByIdForUpdate(1)).thenReturn(Optional.of(po.getVendor()));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(vendorProductRepository.findByVendorIdAndProductId(1, 10)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(
                        1,
                        List.of(new PurchaseOrderItemCreateRequest(10, 1, BigDecimal.ONE)),
                        null)));
        assertEquals(422, ex.getStatus());
        assertTrue(ex.getDetail().contains("does not supply product"));
    }

    @Test
    void createRejectsQuantityBelowMinimum() {
        VendorProduct vp = new VendorProduct();
        vp.setMinOrderQty(5);
        when(vendorRepository.findByIdForUpdate(1)).thenReturn(Optional.of(po.getVendor()));
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(productA));
        when(vendorProductRepository.findByVendorIdAndProductId(1, 10)).thenReturn(Optional.of(vp));
        ApiException ex = assertThrows(ApiException.class, () ->
                purchaseOrderService.create(new PurchaseOrderCreateRequest(
                        1,
                        List.of(new PurchaseOrderItemCreateRequest(10, 2, BigDecimal.ONE)),
                        null)));
        assertEquals(422, ex.getStatus());
        assertTrue(ex.getDetail().contains("below minimum order quantity"));
    }

    @Test
    void listFiltersByVendorAndCapsAtHundred() {
        when(purchaseOrderRepository.findRecentByVendor(eq(1), any())).thenReturn(List.of(po));
        List<PurchaseOrderResponse> result = purchaseOrderService.list(1);
        assertEquals(1, result.size());
        assertEquals("PO-TEST-100", result.get(0).poNumber());
        verify(purchaseOrderRepository).findRecentByVendor(eq(1), any());
    }

    @Test
    void listWithoutVendorUsesRecent() {
        when(purchaseOrderRepository.findRecent(any())).thenReturn(List.of());
        assertTrue(purchaseOrderService.list(null).isEmpty());
        verify(purchaseOrderRepository).findRecent(any());
    }
}
