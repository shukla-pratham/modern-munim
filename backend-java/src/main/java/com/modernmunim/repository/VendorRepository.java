package com.modernmunim.repository;

import com.modernmunim.entity.Vendor;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface VendorRepository extends JpaRepository<Vendor, Integer>, JpaSpecificationExecutor<Vendor> {

    boolean existsByName(String name);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT v FROM Vendor v WHERE v.id = :id")
    Optional<Vendor> findByIdForUpdate(@Param("id") Integer id);
}
