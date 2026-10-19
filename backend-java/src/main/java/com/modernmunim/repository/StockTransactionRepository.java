package com.modernmunim.repository;

import com.modernmunim.entity.StockTransaction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface StockTransactionRepository extends JpaRepository<StockTransaction, Integer> {

    @Query("""
            SELECT t FROM StockTransaction t
            JOIN FETCH t.product
            WHERE (:productId IS NULL OR t.productId = :productId)
            ORDER BY t.createdAt DESC
            """)
    List<StockTransaction> findFiltered(@Param("productId") Integer productId);
}
