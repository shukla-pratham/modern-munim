package com.modernmunim.entity;

/**
 * PO status stored as VARCHAR in PostgreSQL (not a PG enum).
 * Values match FastAPI PurchaseOrderStatus.
 */
public final class PurchaseOrderStatuses {

    public static final String CREATED = "created";
    public static final String ORDERED = "ordered";
    public static final String DELIVERED = "delivered";
    public static final String CANCELLED = "cancelled";

    private PurchaseOrderStatuses() {}
}
