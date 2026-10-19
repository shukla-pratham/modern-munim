package com.modernmunim.repository;

import com.modernmunim.entity.VendorPerformanceMetric;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.OffsetDateTime;
import java.util.List;

public interface VendorPerformanceMetricRepository extends JpaRepository<VendorPerformanceMetric, Integer> {

    List<VendorPerformanceMetric> findByVendorIdAndMetricDateGreaterThanEqualOrderByMetricDateDesc(
            Integer vendorId, OffsetDateTime cutoff);

    List<VendorPerformanceMetric> findTop2ByVendorIdOrderByMetricDateDesc(Integer vendorId);

    void deleteByVendorId(Integer vendorId);
}
