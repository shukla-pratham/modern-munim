package com.modernmunim.repository;

import com.modernmunim.entity.VendorProduct;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface VendorProductRepository extends JpaRepository<VendorProduct, Integer> {

    List<VendorProduct> findByVendorId(Integer vendorId);

    Optional<VendorProduct> findByVendorIdAndProductId(Integer vendorId, Integer productId);

    @Query("SELECT vp FROM VendorProduct vp LEFT JOIN FETCH vp.product WHERE vp.vendorId = :vendorId")
    List<VendorProduct> findByVendorIdWithProduct(@Param("vendorId") Integer vendorId);

    @Query("""
            SELECT vp FROM VendorProduct vp
            JOIN FETCH vp.vendor v
            LEFT JOIN FETCH vp.product
            WHERE vp.productId = :productId AND v.isActive = true
            ORDER BY v.overallScore DESC
            """)
    List<VendorProduct> findActiveByProductIdOrderByVendorScoreDesc(@Param("productId") Integer productId);

    @Query("SELECT AVG(vp.unitCost) FROM VendorProduct vp WHERE vp.productId = :productId")
    BigDecimal averageUnitCostByProductId(@Param("productId") Integer productId);

    void deleteByVendorId(Integer vendorId);
}
