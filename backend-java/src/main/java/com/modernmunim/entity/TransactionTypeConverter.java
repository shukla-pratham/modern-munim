package com.modernmunim.entity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

/**
 * Persist Java {@link TransactionType} wire names ({@code in}/{@code out}) as the live
 * PostgreSQL {@code transactiontype} labels ({@code STOCK_IN}/{@code STOCK_OUT}).
 */
@Converter
public class TransactionTypeConverter implements AttributeConverter<TransactionType, String> {

    @Override
    public String convertToDatabaseColumn(TransactionType attribute) {
        if (attribute == null) {
            return null;
        }
        return switch (attribute) {
            case in -> "in";
            case out -> "out";
        };
    }

    @Override
    public TransactionType convertToEntityAttribute(String dbData) {
        if (dbData == null || dbData.isBlank()) {
            return null;
        }
        String normalized = dbData.trim().toUpperCase();
        return switch (normalized) {
            case "STOCK_IN", "IN" -> TransactionType.in;
            case "STOCK_OUT", "OUT" -> TransactionType.out;
            default -> throw new IllegalArgumentException("Unknown transaction type: " + dbData);
        };
    }
}
