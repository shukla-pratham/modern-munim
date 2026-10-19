package com.modernmunim.repository;

import com.modernmunim.entity.Expense;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

public interface ExpenseRepository extends JpaRepository<Expense, Integer>, JpaSpecificationExecutor<Expense> {

    @Query("SELECT e FROM Expense e LEFT JOIN FETCH e.product WHERE e.id = :id")
    Optional<Expense> findByIdWithProduct(@Param("id") Integer id);

    @Query("""
            SELECT COALESCE(SUM(e.amount), 0)
            FROM Expense e
            WHERE e.createdAt >= :cutoff
            """)
    BigDecimal sumAmountSince(@Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT e.category, COALESCE(SUM(e.amount), 0)
            FROM Expense e
            WHERE e.createdAt >= :cutoff
            GROUP BY e.category
            """)
    List<Object[]> sumAmountByCategorySince(@Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT e.expenseType, COALESCE(SUM(e.amount), 0)
            FROM Expense e
            WHERE e.createdAt >= :cutoff
            GROUP BY e.expenseType
            """)
    List<Object[]> sumAmountByTypeSince(@Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT EXTRACT(YEAR FROM e.createdAt), EXTRACT(MONTH FROM e.createdAt), COALESCE(SUM(e.amount), 0)
            FROM Expense e
            WHERE e.createdAt >= :cutoff
            GROUP BY EXTRACT(YEAR FROM e.createdAt), EXTRACT(MONTH FROM e.createdAt)
            ORDER BY EXTRACT(YEAR FROM e.createdAt), EXTRACT(MONTH FROM e.createdAt)
            """)
    List<Object[]> sumAmountByMonthSince(@Param("cutoff") OffsetDateTime cutoff);

    @Query("""
            SELECT e.productId, COALESCE(SUM(e.amount), 0)
            FROM Expense e
            WHERE e.createdAt >= :cutoff AND e.productId IS NOT NULL
            GROUP BY e.productId
            """)
    List<Object[]> sumAmountByProductSince(@Param("cutoff") OffsetDateTime cutoff);
}
