package com.modernmunim.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Entity
@Table(name = "vendor_performance_metrics")
@Getter
@Setter
@NoArgsConstructor
public class VendorPerformanceMetric {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "vendor_id", nullable = false)
    private Integer vendorId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "vendor_id", insertable = false, updatable = false)
    private Vendor vendor;

    @Column(name = "metric_date", nullable = false)
    private OffsetDateTime metricDate;

    @Column(name = "avg_lead_time", precision = 5, scale = 2)
    private BigDecimal avgLeadTime;

    @Column(name = "on_time_delivery_rate", precision = 5, scale = 2)
    private BigDecimal onTimeDeliveryRate;

    @Column(name = "fulfillment_rate", precision = 5, scale = 2)
    private BigDecimal fulfillmentRate;

    @Column(name = "avg_unit_cost", precision = 10, scale = 2)
    private BigDecimal avgUnitCost;

    @Column(name = "price_variance", precision = 10, scale = 2)
    private BigDecimal priceVariance;

    @Column(name = "delay_days_avg", precision = 5, scale = 2)
    private BigDecimal delayDaysAvg;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @PrePersist
    void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }
}
