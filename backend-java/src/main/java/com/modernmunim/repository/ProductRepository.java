package com.modernmunim.repository;

import com.modernmunim.entity.Product;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface ProductRepository extends JpaRepository<Product, Integer>, JpaSpecificationExecutor<Product> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT p FROM Product p WHERE p.id = :id")
    Optional<Product> findByIdForUpdate(@Param("id") Integer id);

    @Query("SELECT COALESCE(SUM(p.price * p.stockQuantity), 0) FROM Product p")
    BigDecimal sumInventoryValue();

    @Query("SELECT p FROM Product p WHERE p.stockQuantity = 0 ORDER BY p.id")
    List<Product> findOutOfStock();

    @Query("""
            SELECT p FROM Product p
            WHERE p.stockQuantity > 0 AND p.stockQuantity <= p.stockThreshold
            ORDER BY p.id
            """)
    List<Product> findLowStock();
}
