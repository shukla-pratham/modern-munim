package com.modernmunim.repository;

import com.modernmunim.entity.PurchaseOrder;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

public interface PurchaseOrderRepository extends JpaRepository<PurchaseOrder, Integer> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT po FROM PurchaseOrder po WHERE po.id = :id")
    Optional<PurchaseOrder> findByIdForUpdate(@Param("id") Integer id);

    @EntityGraph(attributePaths = {"items", "items.product", "vendor"})
    @Query("SELECT po FROM PurchaseOrder po WHERE po.id = :id")
    Optional<PurchaseOrder> findByIdWithDetails(@Param("id") Integer id);

    boolean existsByVendorId(Integer vendorId);

    @Query("SELECT MAX(po.id) FROM PurchaseOrder po")
    Integer findMaxId();

    @EntityGraph(attributePaths = {"items", "items.product", "vendor"})
    @Query("SELECT po FROM PurchaseOrder po ORDER BY po.orderDate DESC")
    List<PurchaseOrder> findRecent(Pageable pageable);

    @EntityGraph(attributePaths = {"items", "items.product", "vendor"})
    @Query("SELECT po FROM PurchaseOrder po WHERE po.vendorId = :vendorId ORDER BY po.orderDate DESC")
    List<PurchaseOrder> findRecentByVendor(@Param("vendorId") Integer vendorId, Pageable pageable);
}
