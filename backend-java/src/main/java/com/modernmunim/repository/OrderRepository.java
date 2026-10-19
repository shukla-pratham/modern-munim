package com.modernmunim.repository;

import com.modernmunim.entity.Order;
import com.modernmunim.entity.OrderStatus;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

public interface OrderRepository extends JpaRepository<Order, Integer> {

    @EntityGraph(attributePaths = {"items", "items.product"})
    List<Order> findByUserIdOrderByCreatedAtDesc(Integer userId);

    @EntityGraph(attributePaths = {"items", "items.product"})
    List<Order> findAllByOrderByCreatedAtDesc();

    @Override
    @EntityGraph(attributePaths = {"items", "items.product"})
    Optional<Order> findById(Integer id);

    @Query("""
            SELECT COALESCE(SUM(o.totalAmount), 0)
            FROM Order o
            WHERE o.status = :status AND o.createdAt >= :cutoff
            """)
    BigDecimal sumTotalAmountByStatusSince(
            @Param("status") OrderStatus status,
            @Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT COUNT(o)
            FROM Order o
            WHERE o.status = :status AND o.createdAt >= :cutoff
            """)
    long countByStatusSince(
            @Param("status") OrderStatus status,
            @Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT FUNCTION('DATE', o.createdAt), COALESCE(SUM(o.totalAmount), 0)
            FROM Order o
            WHERE o.status = :status AND o.createdAt >= :cutoff
            GROUP BY FUNCTION('DATE', o.createdAt)
            ORDER BY FUNCTION('DATE', o.createdAt)
            """)
    List<Object[]> dailyRevenueByStatusSince(
            @Param("status") OrderStatus status,
            @Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT FUNCTION('DATE', o.createdAt), COUNT(o), COALESCE(SUM(o.totalAmount), 0)
            FROM Order o
            WHERE o.status = :status AND o.createdAt >= :cutoff
            GROUP BY FUNCTION('DATE', o.createdAt)
            ORDER BY FUNCTION('DATE', o.createdAt)
            """)
    List<Object[]> dailySalesByStatusSince(
            @Param("status") OrderStatus status,
            @Param("cutoff") OffsetDateTime cutoff);
}
