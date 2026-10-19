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
import static org.junit.jupiter.api.Assertions.assertTrue;

class OrderPgEnumMappingTest {

    private final OrderStatusConverter orderStatusConverter = new OrderStatusConverter();
    private final TransactionTypeConverter transactionTypeConverter = new TransactionTypeConverter();

    @Test
    void javaOrderStatusPersistsAsLowercasePostgresLabel() {
        assertEquals("pending", orderStatusConverter.convertToDatabaseColumn(OrderStatus.pending));
        assertEquals("completed", orderStatusConverter.convertToDatabaseColumn(OrderStatus.completed));
        assertEquals("cancelled", orderStatusConverter.convertToDatabaseColumn(OrderStatus.cancelled));
    }

    @Test
    void postgresOrderStatusLabelMapsToJavaEnum() {
        assertEquals(OrderStatus.completed, orderStatusConverter.convertToEntityAttribute("COMPLETED"));
        assertEquals(OrderStatus.pending, orderStatusConverter.convertToEntityAttribute("pending"));
    }

    @Test
    void javaTransactionTypePersistsAsPostgresLabels() {
        assertEquals("in", transactionTypeConverter.convertToDatabaseColumn(TransactionType.in));
        assertEquals("out", transactionTypeConverter.convertToDatabaseColumn(TransactionType.out));
    }

    @Test
    void postgresTransactionTypeLabelMapsToJavaEnum() {
        assertEquals(TransactionType.in, transactionTypeConverter.convertToEntityAttribute("STOCK_IN"));
        assertEquals(TransactionType.out, transactionTypeConverter.convertToEntityAttribute("STOCK_OUT"));
        assertEquals(TransactionType.in, transactionTypeConverter.convertToEntityAttribute("in"));
    }

    @Test
    void orderStatusPersistenceUsesConverterAndTextCastNotNamedEnum() throws Exception {
        Field field = Order.class.getDeclaredField("status");
        assertNull(field.getAnnotation(Enumerated.class));
        assertNull(field.getAnnotation(JdbcTypeCode.class));
        Convert convert = field.getAnnotation(Convert.class);
        assertNotNull(convert);
        assertEquals(OrderStatusConverter.class, convert.converter());
        ColumnTransformer transformer = field.getAnnotation(ColumnTransformer.class);
        assertNotNull(transformer);
        assertTrue(transformer.read().contains("::text"));
        assertTrue(transformer.write().contains("::orderstatus"));
    }

    @Test
    void transactionTypePersistenceUsesConverterAndTextCastNotNamedEnum() throws Exception {
        Field field = StockTransaction.class.getDeclaredField("transactionType");
        assertNull(field.getAnnotation(Enumerated.class));
        assertNull(field.getAnnotation(JdbcTypeCode.class));
        Convert convert = field.getAnnotation(Convert.class);
        assertNotNull(convert);
        assertEquals(TransactionTypeConverter.class, convert.converter());
        ColumnTransformer transformer = field.getAnnotation(ColumnTransformer.class);
        assertNotNull(transformer);
        assertTrue(transformer.read().contains("::text"));
        assertTrue(transformer.write().contains("::transactiontype"));
    }
}
