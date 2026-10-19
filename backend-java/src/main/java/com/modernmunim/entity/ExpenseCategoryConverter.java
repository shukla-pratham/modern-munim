package com.modernmunim.entity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

/**
 * Persist Java {@link ExpenseCategory} constants as the live PostgreSQL
 * {@code expensecategory} labels ({@code INVENTORY}, …). HTTP still uses lowercase
 * via {@link ExpenseCategory#apiValue()}. Hibernate NAMED_ENUM cannot be used here.
 */
@Converter
public class ExpenseCategoryConverter implements AttributeConverter<ExpenseCategory, String> {

    @Override
    public String convertToDatabaseColumn(ExpenseCategory attribute) {
        return attribute == null ? null : attribute.apiValue();
    }

    @Override
    public ExpenseCategory convertToEntityAttribute(String dbData) {
        return dbData == null || dbData.isBlank() ? null : ExpenseCategory.fromApi(dbData);
    }
}
