package com.modernmunim.entity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

/**
 * Persist Java {@link ExpenseType} constants as the live PostgreSQL
 * {@code expensetype} labels ({@code ONE_TIME}, {@code RECURRING}). HTTP still uses
 * lowercase snake_case via {@link ExpenseType#apiValue()}.
 */
@Converter
public class ExpenseTypeConverter implements AttributeConverter<ExpenseType, String> {

    @Override
    public String convertToDatabaseColumn(ExpenseType attribute) {
        return attribute == null ? null : attribute.apiValue();
    }

    @Override
    public ExpenseType convertToEntityAttribute(String dbData) {
        return dbData == null || dbData.isBlank() ? null : ExpenseType.fromApi(dbData);
    }
}
