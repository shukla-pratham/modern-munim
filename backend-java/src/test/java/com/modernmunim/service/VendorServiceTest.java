package com.modernmunim.service;

import com.modernmunim.dto.BestVendorResponse;
import com.modernmunim.dto.VendorCreateRequest;
import com.modernmunim.dto.VendorCreateResponse;
import com.modernmunim.dto.VendorProductCreateRequest;
import com.modernmunim.dto.VendorProductResponse;
import com.modernmunim.dto.VendorRankingResponse;
import com.modernmunim.dto.VendorScorecardResponse;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.Vendor;
import com.modernmunim.entity.VendorPerformanceMetric;
import com.modernmunim.entity.VendorProduct;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.PurchaseOrderRepository;
import com.modernmunim.repository.VendorPerformanceMetricRepository;
import com.modernmunim.repository.VendorProductRepository;
import com.modernmunim.repository.VendorRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class VendorServiceTest {

    @Mock
    private VendorRepository vendorRepository;
    @Mock
    private VendorProductRepository vendorProductRepository;
    @Mock
    private VendorPerformanceMetricRepository vendorPerformanceMetricRepository;
    @Mock
    private PurchaseOrderRepository purchaseOrderRepository;
    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private VendorService vendorService;

    private Vendor vendor;
    private Product product;

    @BeforeEach
    void setUp() {
        vendor = new Vendor();
        vendor.setId(1);
        vendor.setName("Acme Supply");
        vendor.setIsActive(true);
        vendor.setAvgLeadTimeDays(5);
        vendor.setReliabilityScore(new BigDecimal("90.00"));
        vendor.setCostScore(new BigDecimal("80.00"));
        vendor.setOverallScore(new BigDecimal("85.00"));

        product = new Product();
        product.setId(10);
        product.setName("Widget");
        product.setPrice(new BigDecimal("5.00"));
        product.setStockQuantity(3);
    }

    @Test
    void createPersistsDefaultsAndScores() {
        when(vendorRepository.existsByName("Acme Supply")).thenReturn(false);
        when(vendorRepository.save(any())).thenAnswer(inv -> {
            Vendor v = inv.getArgument(0);
            v.setId(42);
            return v;
        });

        VendorCreateResponse response = vendorService.create(
                new VendorCreateRequest("Acme Supply", null, 7,
                        new BigDecimal("70.00"), new BigDecimal("60.00"), new BigDecimal("65.00")));

        assertEquals(42, response.id());
        assertEquals("Acme Supply", response.name());
        assertEquals(true, response.isActive());
        assertEquals(7, response.avgLeadTimeDays());
        assertEquals(new BigDecimal("70.00"), response.reliabilityScore());

        ArgumentCaptor<Vendor> captor = ArgumentCaptor.forClass(Vendor.class);
        verify(vendorRepository).save(captor.capture());
        assertEquals(true, captor.getValue().getIsActive());
        verifyNoInteractions(productRepository);
    }

    @Test
    void createDuplicateNameReturns400() {
        when(vendorRepository.existsByName("Acme Supply")).thenReturn(true);
        ApiException ex = assertThrows(ApiException.class, () ->
                vendorService.create(new VendorCreateRequest("Acme Supply", true, null, null, null, null)));
        assertEquals(400, ex.getStatus());
        assertEquals("Vendor with this name already exists", ex.getDetail());
        verify(vendorRepository, never()).save(any());
    }

    @Test
    void rankingsReturnsActiveVendorsWithExplanations() {
        when(vendorRepository.findAll(any(Specification.class), any(Sort.class)))
                .thenReturn(List.of(vendor));

        List<VendorRankingResponse> page = vendorService.rankings(null, null, null);

        assertEquals(1, page.size());
        assertEquals(1, page.get(0).vendorId());
        assertEquals("Acme Supply", page.get(0).vendorName());
        assertTrue(page.get(0).explanation().startsWith("Rank #1."));
        assertTrue(page.get(0).explanation().contains("Overall score: 85.0/100"));
    }

    @Test
    void rankingsEmptyExplanationWhenNoScores() {
        Vendor blank = new Vendor();
        blank.setId(2);
        blank.setName("NewCo");
        blank.setIsActive(true);
        when(vendorRepository.findAll(any(Specification.class), any(Sort.class)))
                .thenReturn(List.of(blank));

        List<VendorRankingResponse> page = vendorService.rankings(null, null, null);
        assertEquals("No performance data", page.get(0).explanation());
    }

    @Test
    void getVendorProductsRequiresActiveVendor() {
        vendor.setIsActive(false);
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.listVendorProducts(1));
        assertEquals(404, ex.getStatus());
        assertEquals("Vendor not found", ex.getDetail());
        verify(vendorProductRepository, never()).findByVendorIdWithProduct(any());
    }

    @Test
    void getVendorProductsMissingVendor404() {
        when(vendorRepository.findById(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.listVendorProducts(99));
        assertEquals(404, ex.getStatus());
    }

    @Test
    void getVendorProductsMapsCatalog() {
        VendorProduct vp = new VendorProduct();
        vp.setId(3);
        vp.setVendorId(1);
        vp.setProductId(10);
        vp.setProduct(product);
        vp.setUnitCost(new BigDecimal("4.50"));
        vp.setMinOrderQty(2);
        vp.setLeadTimeDays(4);
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        when(vendorProductRepository.findByVendorIdWithProduct(1)).thenReturn(List.of(vp));

        List<VendorProductResponse> list = vendorService.listVendorProducts(1);
        assertEquals(1, list.size());
        assertEquals(3, list.get(0).vendorProductId());
        assertEquals("Widget", list.get(0).productName());
        assertEquals(new BigDecimal("4.50"), list.get(0).unitCost());
        assertEquals(2, list.get(0).minOrderQty());
    }

    @Test
    void addProductSuccessAndClampsMinQty() {
        when(vendorRepository.existsById(1)).thenReturn(true);
        when(productRepository.findById(10)).thenReturn(Optional.of(product));
        when(vendorProductRepository.findByVendorIdAndProductId(1, 10)).thenReturn(Optional.empty());
        when(vendorProductRepository.save(any())).thenAnswer(inv -> {
            VendorProduct vp = inv.getArgument(0);
            vp.setId(9);
            return vp;
        });

        VendorProductResponse response = vendorService.addProduct(
                1, new VendorProductCreateRequest(10, new BigDecimal("1.25"), 0, 3));

        assertEquals(9, response.vendorProductId());
        assertEquals("Widget", response.productName());
        ArgumentCaptor<VendorProduct> captor = ArgumentCaptor.forClass(VendorProduct.class);
        verify(vendorProductRepository).save(captor.capture());
        assertEquals(1, captor.getValue().getMinOrderQty());
    }

    @Test
    void addProductDuplicateReturns400() {
        when(vendorRepository.existsById(1)).thenReturn(true);
        when(productRepository.findById(10)).thenReturn(Optional.of(product));
        when(vendorProductRepository.findByVendorIdAndProductId(1, 10)).thenReturn(Optional.of(new VendorProduct()));

        ApiException ex = assertThrows(ApiException.class, () ->
                vendorService.addProduct(1, new VendorProductCreateRequest(10, new BigDecimal("1.00"), 1, null)));
        assertEquals(400, ex.getStatus());
        assertEquals("Vendor already supplies this product", ex.getDetail());
        verify(vendorProductRepository, never()).save(any());
    }

    @Test
    void addProductMissingProduct404() {
        when(vendorRepository.existsById(1)).thenReturn(true);
        when(productRepository.findById(10)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () ->
                vendorService.addProduct(1, new VendorProductCreateRequest(10, new BigDecimal("1.00"), 1, null)));
        assertEquals(404, ex.getStatus());
        assertEquals("Product not found", ex.getDetail());
    }

    @Test
    void deleteMissingVendor404() {
        when(vendorRepository.findById(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.delete(99));
        assertEquals(404, ex.getStatus());
        verify(vendorRepository, never()).delete(any(Vendor.class));
    }

    @Test
    void deleteBlockedWhenPurchaseOrdersExist() {
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        when(purchaseOrderRepository.existsByVendorId(1)).thenReturn(true);

        ApiException ex = assertThrows(ApiException.class, () -> vendorService.delete(1));
        assertEquals(400, ex.getStatus());
        assertTrue(ex.getDetail().contains("Cannot delete vendor with existing purchase orders"));
        verify(vendorRepository, never()).delete(any(Vendor.class));
        verify(vendorProductRepository, never()).deleteByVendorId(any());
    }

    @Test
    void deleteRemovesCatalogAndMetricsNotStock() {
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        when(purchaseOrderRepository.existsByVendorId(1)).thenReturn(false);

        vendorService.delete(1);

        verify(vendorProductRepository).deleteByVendorId(1);
        verify(vendorPerformanceMetricRepository).deleteByVendorId(1);
        verify(vendorRepository).delete(vendor);
        verifyNoInteractions(productRepository);
    }

    @Test
    void bestForProductMissingProduct404() {
        when(productRepository.existsById(10)).thenReturn(false);
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.bestForProduct(10));
        assertEquals(404, ex.getStatus());
        assertEquals("Product not found", ex.getDetail());
    }

    @Test
    void bestForProductNoActiveVendors404() {
        when(productRepository.existsById(10)).thenReturn(true);
        when(vendorProductRepository.findActiveByProductIdOrderByVendorScoreDesc(10)).thenReturn(List.of());
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.bestForProduct(10));
        assertEquals(404, ex.getStatus());
        assertEquals("No active vendors supply this product", ex.getDetail());
    }

    @Test
    void bestForProductRecommendsHighestComposite() {
        Vendor other = new Vendor();
        other.setId(2);
        other.setName("Budget");
        other.setIsActive(true);
        other.setOverallScore(new BigDecimal("40.00"));
        other.setReliabilityScore(new BigDecimal("50.00"));

        VendorProduct cheap = catalog(vendor, new BigDecimal("10.00"), 2);
        VendorProduct expensive = catalog(other, new BigDecimal("20.00"), 8);

        when(productRepository.existsById(10)).thenReturn(true);
        when(vendorProductRepository.findActiveByProductIdOrderByVendorScoreDesc(10))
                .thenReturn(List.of(cheap, expensive));
        when(vendorProductRepository.averageUnitCostByProductId(10)).thenReturn(new BigDecimal("15.00"));

        BestVendorResponse response = vendorService.bestForProduct(10);
        assertEquals(1, response.recommendedVendor().vendorId());
        assertEquals("Acme Supply", response.recommendedVendor().vendorName());
        assertEquals(1, response.alternatives().size());
        assertEquals(2, response.alternatives().get(0).vendorId());
        assertTrue(response.reasoning().startsWith("Recommended: Acme Supply"));
    }

    @Test
    void scorecardStableWhenInsufficientMetrics() {
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        when(vendorPerformanceMetricRepository.findTop2ByVendorIdOrderByMetricDateDesc(1))
                .thenReturn(List.of());

        VendorScorecardResponse card = vendorService.scorecard(1);
        assertEquals("stable", card.reliabilityTrend());
        assertEquals("✅ Top performer - Recommended vendor", card.actionInsights().get(0));
    }

    @Test
    void scorecardRisingTrendFromOnTimeDelivery() {
        VendorPerformanceMetric recent = metric(new BigDecimal("90.00"), new BigDecimal("2.00"), new BigDecimal("1.00"));
        VendorPerformanceMetric previous = metric(new BigDecimal("80.00"), new BigDecimal("2.00"), new BigDecimal("1.00"));
        when(vendorRepository.findById(1)).thenReturn(Optional.of(vendor));
        when(vendorPerformanceMetricRepository.findTop2ByVendorIdOrderByMetricDateDesc(1))
                .thenReturn(List.of(recent, previous));

        VendorScorecardResponse card = vendorService.scorecard(1);
        assertEquals("rising", card.reliabilityTrend());
    }

    @Test
    void performanceMissingVendor404() {
        when(vendorRepository.findById(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> vendorService.performance(99, 30));
        assertEquals(404, ex.getStatus());
    }

    @Test
    void pythonTruthyTreatsZeroAsFalse() {
        assertFalse(VendorService.pythonTruthy(BigDecimal.ZERO));
        assertFalse(VendorService.pythonTruthy(0));
        assertTrue(VendorService.pythonTruthy(new BigDecimal("0.01")));
    }

    private VendorProduct catalog(Vendor owner, BigDecimal unitCost, Integer lead) {
        VendorProduct vp = new VendorProduct();
        vp.setVendorId(owner.getId());
        vp.setVendor(owner);
        vp.setProductId(10);
        vp.setProduct(product);
        vp.setUnitCost(unitCost);
        vp.setMinOrderQty(1);
        vp.setLeadTimeDays(lead);
        return vp;
    }

    private static VendorPerformanceMetric metric(BigDecimal otd, BigDecimal variance, BigDecimal delay) {
        VendorPerformanceMetric m = new VendorPerformanceMetric();
        m.setOnTimeDeliveryRate(otd);
        m.setPriceVariance(variance);
        m.setDelayDaysAvg(delay);
        m.setMetricDate(OffsetDateTime.parse("2026-08-01T00:00:00Z"));
        return m;
    }
}
