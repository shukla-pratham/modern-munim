package com.modernmunim.service;

import com.modernmunim.dto.BestVendorResponse;
import com.modernmunim.dto.VendorComparisonResponse;
import com.modernmunim.dto.VendorCreateRequest;
import com.modernmunim.dto.VendorCreateResponse;
import com.modernmunim.dto.VendorPerformanceResponse;
import com.modernmunim.dto.VendorProductCreateRequest;
import com.modernmunim.dto.VendorProductResponse;
import com.modernmunim.dto.VendorRankingResponse;
import com.modernmunim.dto.VendorScorecardResponse;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.Vendor;
import com.modernmunim.entity.VendorPerformanceMetric;
import com.modernmunim.entity.VendorProduct;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.PurchaseOrderRepository;
import com.modernmunim.repository.VendorPerformanceMetricRepository;
import com.modernmunim.repository.VendorProductRepository;
import com.modernmunim.repository.VendorRepository;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;
import jakarta.persistence.criteria.Subquery;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Mirrors FastAPI {@code app/api/vendors.py}. Vendor CRUD/catalog/rankings only;
 * does not mutate product stock or stock_transactions.
 */
@Service
@RequiredArgsConstructor
public class VendorService {

    private static final BigDecimal HUNDRED = new BigDecimal("100");
    private static final BigDecimal FIVE = new BigDecimal("5");
    private static final BigDecimal FIFTY = new BigDecimal("50");
    private static final BigDecimal SIXTY = new BigDecimal("60");
    private static final BigDecimal EIGHTY = new BigDecimal("80");
    private static final BigDecimal TEN = new BigDecimal("10");

    private final VendorRepository vendorRepository;
    private final VendorProductRepository vendorProductRepository;
    private final VendorPerformanceMetricRepository vendorPerformanceMetricRepository;
    private final PurchaseOrderRepository purchaseOrderRepository;
    private final ProductRepository productRepository;

    @Transactional
    public VendorCreateResponse create(VendorCreateRequest request) {
        if (vendorRepository.existsByName(request.name())) {
            throw DomainExceptions.vendorNameExists();
        }
        Vendor vendor = new Vendor();
        vendor.setName(request.name());
        vendor.setIsActive(request.isActive() != null ? request.isActive() : true);
        vendor.setAvgLeadTimeDays(request.avgLeadTimeDays());
        vendor.setReliabilityScore(request.reliabilityScore());
        vendor.setCostScore(request.costScore());
        vendor.setOverallScore(request.overallScore());
        Vendor saved = vendorRepository.save(vendor);
        return DtoMapper.toVendorCreateResponse(saved);
    }

    @Transactional
    public void delete(Integer vendorId) {
        Vendor vendor = vendorRepository.findById(vendorId)
                .orElseThrow(DomainExceptions::vendorNotFound);
        if (purchaseOrderRepository.existsByVendorId(vendorId)) {
            throw DomainExceptions.vendorHasPurchaseOrders();
        }
        // ORM-equivalent of SQLAlchemy cascade="all, delete-orphan" on catalog/metrics.
        // purchase_orders are intentionally NOT cascaded (application 400 above; DB FK NO ACTION).
        vendorProductRepository.deleteByVendorId(vendorId);
        vendorPerformanceMetricRepository.deleteByVendorId(vendorId);
        vendorRepository.delete(vendor);
    }

    @Transactional(readOnly = true)
    public List<VendorRankingResponse> rankings(Integer productId, BigDecimal minReliability, BigDecimal maxCost) {
        Specification<Vendor> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            predicates.add(cb.equal(root.get("isActive"), true));

            if (productId != null) {
                Subquery<Integer> sub = query.subquery(Integer.class);
                Root<VendorProduct> vp = sub.from(VendorProduct.class);
                sub.select(vp.get("vendorId")).where(cb.equal(vp.get("productId"), productId));
                predicates.add(root.get("id").in(sub));
            }

            if (minReliability != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("reliabilityScore"), minReliability));
            }

            // FastAPI: max_cost is applied only when product_id is also provided.
            if (maxCost != null && productId != null) {
                Subquery<Integer> cheap = query.subquery(Integer.class);
                Root<VendorProduct> vp = cheap.from(VendorProduct.class);
                cheap.select(vp.get("vendorId")).where(
                        cb.equal(vp.get("productId"), productId),
                        cb.lessThanOrEqualTo(vp.get("unitCost"), maxCost)
                );
                predicates.add(root.get("id").in(cheap));
            }

            return cb.and(predicates.toArray(Predicate[]::new));
        };

        // SQLAlchemy desc(overall_score) with no NULLS clause. Do not use Sort.NullHandling:
        // Hibernate Criteria rejects "Applying Null Precedence using Criteria Queries".
        // PostgreSQL DESC default is NULLS FIRST, matching that SQL.
        Sort sort = Sort.by(Sort.Direction.DESC, "overallScore");
        List<Vendor> vendors = vendorRepository.findAll(spec, sort);

        List<VendorRankingResponse> results = new ArrayList<>();
        for (int i = 0; i < vendors.size(); i++) {
            results.add(toRanking(vendors.get(i), i + 1));
        }
        return results;
    }

    @Transactional(readOnly = true)
    public List<VendorProductResponse> listVendorProducts(Integer vendorId) {
        Vendor vendor = vendorRepository.findById(vendorId)
                .orElseThrow(DomainExceptions::vendorNotFound);
        if (!Boolean.TRUE.equals(vendor.getIsActive())) {
            throw DomainExceptions.vendorNotFound();
        }
        return vendorProductRepository.findByVendorIdWithProduct(vendorId).stream()
                .map(DtoMapper::toVendorProductResponse)
                .toList();
    }

    @Transactional
    public VendorProductResponse addProduct(Integer vendorId, VendorProductCreateRequest request) {
        if (!vendorRepository.existsById(vendorId)) {
            throw DomainExceptions.vendorNotFound();
        }
        Product product = productRepository.findById(request.productId())
                .orElseThrow(DomainExceptions::productNotFound);
        if (vendorProductRepository.findByVendorIdAndProductId(vendorId, request.productId()).isPresent()) {
            throw DomainExceptions.vendorAlreadySuppliesProduct();
        }

        int minQty = request.minOrderQty() == null ? 1 : Math.max(1, request.minOrderQty());
        VendorProduct vp = new VendorProduct();
        vp.setVendorId(vendorId);
        vp.setProductId(request.productId());
        vp.setUnitCost(request.unitCost());
        vp.setMinOrderQty(minQty);
        vp.setLeadTimeDays(request.leadTimeDays());
        VendorProduct saved = vendorProductRepository.save(vp);
        saved.setProduct(product);
        return DtoMapper.toVendorProductResponse(saved);
    }

    @Transactional(readOnly = true)
    public BestVendorResponse bestForProduct(Integer productId) {
        if (!productRepository.existsById(productId)) {
            throw DomainExceptions.productNotFound();
        }
        List<VendorProduct> vendorProducts = vendorProductRepository
                .findActiveByProductIdOrderByVendorScoreDesc(productId);
        if (vendorProducts.isEmpty()) {
            throw DomainExceptions.noActiveVendorsSupplyProduct();
        }

        // FastAPI computes AVG(unit_cost) for the product across all vendor_products (not only active).
        BigDecimal avgCost = vendorProductRepository.averageUnitCostByProductId(productId);

        List<ScoredVendorProduct> scored = new ArrayList<>();
        for (VendorProduct vp : vendorProducts) {
            Vendor vendor = vp.getVendor();
            BigDecimal overall = vendor.getOverallScore();
            double baseScore = pythonTruthy(overall) ? overall.doubleValue() : 50.0;

            double costFactor = 50.0;
            if (pythonTruthy(avgCost) && pythonTruthy(vp.getUnitCost())) {
                costFactor = 100.0 - ((vp.getUnitCost().doubleValue() / avgCost.doubleValue() - 1.0) * 50.0);
                costFactor = Math.max(0.0, Math.min(100.0, costFactor));
            }
            double composite = (baseScore * 0.6) + (costFactor * 0.4);
            scored.add(new ScoredVendorProduct(vendor, vp, composite));
        }
        scored.sort(Comparator.comparingDouble(ScoredVendorProduct::composite).reversed());

        ScoredVendorProduct recommended = scored.get(0);
        List<VendorRankingResponse> alternatives = new ArrayList<>();
        for (int i = 1; i < Math.min(3, scored.size()); i++) {
            alternatives.add(toBestForProductRanking(scored.get(i), i + 1));
        }

        List<String> reasoningParts = new ArrayList<>();
        reasoningParts.add("Recommended: " + recommended.vendor().getName());
        if (pythonTruthy(recommended.vendor().getOverallScore())) {
            reasoningParts.add("Overall score: " + formatOneDecimal(recommended.vendor().getOverallScore()) + "/100");
        }
        if (pythonTruthy(recommended.vendorProduct().getUnitCost())) {
            reasoningParts.add("Unit cost: $" + formatTwoDecimal(recommended.vendorProduct().getUnitCost()));
        }
        if (pythonTruthy(recommended.vendor().getReliabilityScore())) {
            reasoningParts.add("Reliability: " + formatOneDecimal(recommended.vendor().getReliabilityScore()) + "/100");
        }

        return new BestVendorResponse(
                toBestForProductRanking(recommended, 1),
                alternatives,
                String.join(". ", reasoningParts)
        );
    }

    @Transactional(readOnly = true)
    public List<VendorComparisonResponse> compareForProduct(Integer productId) {
        if (!productRepository.existsById(productId)) {
            throw DomainExceptions.productNotFound();
        }
        List<VendorProduct> vendorProducts = vendorProductRepository
                .findActiveByProductIdOrderByVendorScoreDesc(productId);
        List<VendorComparisonResponse> results = new ArrayList<>();
        for (VendorProduct vp : vendorProducts) {
            Vendor vendor = vp.getVendor();
            BigDecimal risk = pythonTruthy(vendor.getReliabilityScore())
                    ? HUNDRED.subtract(vendor.getReliabilityScore())
                    : null;
            Integer lead = pythonTruthy(vp.getLeadTimeDays())
                    ? vp.getLeadTimeDays()
                    : vendor.getAvgLeadTimeDays();
            results.add(new VendorComparisonResponse(
                    vendor.getId(),
                    vendor.getName(),
                    vp.getUnitCost(),
                    vendor.getReliabilityScore(),
                    lead,
                    risk,
                    vendor.getOverallScore()
            ));
        }
        return results;
    }

    @Transactional(readOnly = true)
    public List<VendorPerformanceResponse> performance(Integer vendorId, int days) {
        Vendor vendor = vendorRepository.findById(vendorId)
                .orElseThrow(DomainExceptions::vendorNotFound);
        OffsetDateTime cutoff = OffsetDateTime.now().minusDays(days);
        return vendorPerformanceMetricRepository
                .findByVendorIdAndMetricDateGreaterThanEqualOrderByMetricDateDesc(vendorId, cutoff)
                .stream()
                .map(metric -> DtoMapper.toVendorPerformanceResponse(vendor, metric))
                .toList();
    }

    @Transactional(readOnly = true)
    public VendorScorecardResponse scorecard(Integer vendorId) {
        Vendor vendor = vendorRepository.findById(vendorId)
                .orElseThrow(DomainExceptions::vendorNotFound);
        List<VendorPerformanceMetric> metrics = vendorPerformanceMetricRepository
                .findTop2ByVendorIdOrderByMetricDateDesc(vendorId);

        BigDecimal currentReliability = vendor.getReliabilityScore();
        String reliabilityTrend = "stable";
        if (metrics.size() >= 2) {
            BigDecimal recentOtd = metrics.get(0).getOnTimeDeliveryRate();
            BigDecimal previousOtd = metrics.get(1).getOnTimeDeliveryRate();
            if (pythonTruthy(recentOtd) && pythonTruthy(previousOtd)) {
                if (recentOtd.compareTo(previousOtd.add(FIVE)) > 0) {
                    reliabilityTrend = "rising";
                } else if (recentOtd.compareTo(previousOtd.subtract(FIVE)) < 0) {
                    reliabilityTrend = "declining";
                }
            }
        }

        BigDecimal costVolatility = null;
        BigDecimal delayTrend = null;
        if (!metrics.isEmpty()) {
            VendorPerformanceMetric latest = metrics.get(0);
            if (pythonTruthy(latest.getPriceVariance())) {
                costVolatility = latest.getPriceVariance();
            }
            if (pythonTruthy(latest.getDelayDaysAvg())) {
                delayTrend = latest.getDelayDaysAvg();
            }
        }

        List<String> insights = new ArrayList<>();
        if (pythonTruthy(vendor.getOverallScore())) {
            if (vendor.getOverallScore().compareTo(FIFTY) < 0) {
                insights.add("⚠️ Avoid vendor this week - Low overall score");
            } else if (pythonTruthy(vendor.getReliabilityScore())
                    && vendor.getReliabilityScore().compareTo(SIXTY) < 0) {
                insights.add("⚠️ High delay risk - Consider alternatives");
            } else if (pythonTruthy(vendor.getCostScore())
                    && vendor.getCostScore().compareTo(FIFTY) < 0) {
                insights.add("💰 Reliable but expensive - Premium pricing");
            } else if (vendor.getOverallScore().compareTo(EIGHTY) > 0) {
                insights.add("✅ Top performer - Recommended vendor");
            }
        }
        if (pythonTruthy(delayTrend) && delayTrend.compareTo(FIVE) > 0) {
            insights.add("🚨 High average delays - Monitor closely");
        }
        if (pythonTruthy(costVolatility) && costVolatility.compareTo(TEN) > 0) {
            insights.add("📊 High price volatility - Inconsistent pricing");
        }
        if (insights.isEmpty()) {
            insights.add("✅ No issues detected");
        }

        return new VendorScorecardResponse(
                vendor.getId(),
                vendor.getName(),
                currentReliability,
                reliabilityTrend,
                vendor.getCostScore(),
                costVolatility,
                delayTrend,
                vendor.getOverallScore(),
                insights
        );
    }

    private static VendorRankingResponse toRanking(Vendor vendor, int rank) {
        List<String> parts = new ArrayList<>();
        if (vendor.getOverallScore() != null) {
            parts.add("Overall score: " + formatOneDecimal(vendor.getOverallScore()) + "/100");
        }
        if (vendor.getReliabilityScore() != null) {
            parts.add("Reliability: " + formatOneDecimal(vendor.getReliabilityScore()) + "/100");
        }
        if (vendor.getCostScore() != null) {
            parts.add("Cost: " + formatOneDecimal(vendor.getCostScore()) + "/100");
        }
        if (vendor.getAvgLeadTimeDays() != null) {
            parts.add("Avg lead time: " + vendor.getAvgLeadTimeDays() + " days");
        }
        String explanation = parts.isEmpty()
                ? "No performance data"
                : "Rank #" + rank + ". " + String.join(" | ", parts);
        return new VendorRankingResponse(
                vendor.getId(),
                vendor.getName() == null ? null : String.valueOf(vendor.getName()),
                vendor.getOverallScore(),
                vendor.getReliabilityScore(),
                vendor.getCostScore(),
                vendor.getAvgLeadTimeDays(),
                Boolean.TRUE.equals(vendor.getIsActive()),
                explanation
        );
    }

    private static VendorRankingResponse toBestForProductRanking(ScoredVendorProduct scored, int rank) {
        Vendor vendor = scored.vendor();
        VendorProduct vp = scored.vendorProduct();
        List<String> parts = new ArrayList<>();
        if (pythonTruthy(vendor.getOverallScore())) {
            parts.add("Overall: " + formatOneDecimal(vendor.getOverallScore()) + "/100");
        }
        parts.add("Unit cost: $" + formatTwoDecimal(vp.getUnitCost()));
        if (pythonTruthy(vp.getLeadTimeDays())) {
            parts.add("Lead time: " + vp.getLeadTimeDays() + " days");
        }
        return new VendorRankingResponse(
                vendor.getId(),
                vendor.getName(),
                vendor.getOverallScore(),
                vendor.getReliabilityScore(),
                vendor.getCostScore(),
                vendor.getAvgLeadTimeDays(),
                vendor.getIsActive(),
                "Rank #" + rank + ". " + String.join(" | ", parts)
        );
    }

    /** Python truthiness: None/0/0.00 are false. */
    static boolean pythonTruthy(BigDecimal value) {
        return value != null && value.compareTo(BigDecimal.ZERO) != 0;
    }

    static boolean pythonTruthy(Integer value) {
        return value != null && value != 0;
    }

    static String formatOneDecimal(BigDecimal value) {
        return String.format(Locale.US, "%.1f", value.doubleValue());
    }

    static String formatTwoDecimal(BigDecimal value) {
        return String.format(Locale.US, "%.2f", value.setScale(2, RoundingMode.HALF_UP).doubleValue());
    }

    private record ScoredVendorProduct(Vendor vendor, VendorProduct vendorProduct, double composite) {}
}
