package com.modernmunim.entity;

import jakarta.persistence.Convert;
import jakarta.persistence.Enumerated;
import org.hibernate.annotations.ColumnTransformer;
import org.hibernate.annotations.JdbcTypeCode;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ExpensePgEnumMappingTest {

    private final ExpenseCategoryConverter categoryConverter = new ExpenseCategoryConverter();
    private final ExpenseTypeConverter typeConverter = new ExpenseTypeConverter();

    @Test
    void javaCategoryPersistsAsLowercasePostgresLabel() {
        assertEquals("inventory", categoryConverter.convertToDatabaseColumn(ExpenseCategory.INVENTORY));
        assertEquals("operations", categoryConverter.convertToDatabaseColumn(ExpenseCategory.OPERATIONS));
        assertEquals("marketing", categoryConverter.convertToDatabaseColumn(ExpenseCategory.MARKETING));
    }

    @Test
    void postgresCategoryLabelMapsToJavaEnum() {
        assertEquals(ExpenseCategory.INVENTORY, categoryConverter.convertToEntityAttribute("inventory"));
        assertEquals(ExpenseCategory.OPERATIONS, categoryConverter.convertToEntityAttribute("OPERATIONS"));
    }

    @Test
    void javaExpenseTypePersistsAsLowercasePostgresLabel() {
        assertEquals("one_time", typeConverter.convertToDatabaseColumn(ExpenseType.ONE_TIME));
        assertEquals("recurring", typeConverter.convertToDatabaseColumn(ExpenseType.RECURRING));
    }

    @Test
    void postgresExpenseTypeLabelMapsToJavaEnum() {
        assertEquals(ExpenseType.ONE_TIME, typeConverter.convertToEntityAttribute("one_time"));
        assertEquals(ExpenseType.RECURRING, typeConverter.convertToEntityAttribute("recurring"));
    }

    @Test
    void apiWireValuesStayLowercase() {
        assertEquals("marketing", ExpenseCategory.MARKETING.apiValue());
        assertEquals("one_time", ExpenseType.ONE_TIME.apiValue());
        assertEquals(ExpenseCategory.MARKETING, ExpenseCategory.fromApi("marketing"));
        assertEquals(ExpenseType.RECURRING, ExpenseType.fromApi("recurring"));
    }

    @Test
    void invalidApiEnumIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> ExpenseCategory.fromApi("payroll"));
        assertThrows(IllegalArgumentException.class, () -> ExpenseType.fromApi("monthly"));
    }

    @Test
    void categoryPersistenceUsesConverterAndTextCastNotNamedEnum() throws Exception {
        Field field = Expense.class.getDeclaredField("category");
        assertNull(field.getAnnotation(Enumerated.class));
        assertNull(field.getAnnotation(JdbcTypeCode.class),
                "NAMED_ENUM JdbcTypeCode would bind Java names (INVENTORY) against lowercase PG labels");
        Convert convert = field.getAnnotation(Convert.class);
        assertNotNull(convert);
        assertEquals(ExpenseCategoryConverter.class, convert.converter());
        ColumnTransformer transformer = field.getAnnotation(ColumnTransformer.class);
        assertNotNull(transformer);
        assertTrue(transformer.read().contains("::text"));
        assertTrue(transformer.write().contains("::expensecategory"));
    }

    @Test
    void expenseTypePersistenceUsesConverterAndTextCastNotNamedEnum() throws Exception {
        Field field = Expense.class.getDeclaredField("expenseType");
        assertNull(field.getAnnotation(Enumerated.class));
        assertNull(field.getAnnotation(JdbcTypeCode.class));
        Convert convert = field.getAnnotation(Convert.class);
        assertNotNull(convert);
        assertEquals(ExpenseTypeConverter.class, convert.converter());
        ColumnTransformer transformer = field.getAnnotation(ColumnTransformer.class);
        assertNotNull(transformer);
        assertTrue(transformer.read().contains("::text"));
        assertTrue(transformer.write().contains("::expensetype"));
    }
}
