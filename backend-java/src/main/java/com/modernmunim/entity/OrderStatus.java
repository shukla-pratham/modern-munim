package com.modernmunim.entity;

/**
 * Java constants stay lowercase for the FastAPI wire format ({@code completed}).
 * Live PostgreSQL {@code orderstatus} labels are uppercase ({@code COMPLETED}).
 * Persistence uses {@link OrderStatusConverter}.
 */
public enum OrderStatus {
    pending,
    completed,
    cancelled
}
