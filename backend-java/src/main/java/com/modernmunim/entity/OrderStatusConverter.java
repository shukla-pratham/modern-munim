package com.modernmunim.entity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

/**
 * Persist Java {@link OrderStatus} constants ({@code completed}, …) as the live PostgreSQL
 * {@code orderstatus} labels ({@code COMPLETED}, …). Hibernate NAMED_ENUM would bind the
 * lowercase Java names and fail against this schema.
 */
@Converter
public class OrderStatusConverter implements AttributeConverter<OrderStatus, String> {

    @Override
    public String convertToDatabaseColumn(OrderStatus attribute) {
        return attribute == null ? null : attribute.name();
    }

    @Override
    public OrderStatus convertToEntityAttribute(String dbData) {
        if (dbData == null || dbData.isBlank()) {
            return null;
        }
        return OrderStatus.valueOf(dbData.trim().toLowerCase());
    }
}
