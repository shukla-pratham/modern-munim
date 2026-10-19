package com.modernmunim.repository;

import com.modernmunim.entity.OrderItem;
import com.modernmunim.entity.OrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.OffsetDateTime;
import java.util.List;

public interface OrderItemRepository extends JpaRepository<OrderItem, Integer> {

    @Query("""
            SELECT i.productId, p.name, SUM(i.quantity), SUM(i.quantity * i.priceAtPurchase)
            FROM OrderItem i
            JOIN i.order o
            JOIN i.product p
            WHERE o.status = :status AND o.createdAt >= :cutoff
            GROUP BY i.productId, p.name
            ORDER BY i.productId
            """)
    List<Object[]> aggregateProductSales(
            @Param("status") OrderStatus status,
            @Param("cutoff") OffsetDateTime cutoff);
}
