package com.modernmunim.service;

import com.modernmunim.dto.StockTransactionResponse;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.TransactionType;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.StockTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class InventoryServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockTransactionRepository stockTransactionRepository;

    @InjectMocks
    private InventoryService inventoryService;

    private Product product;

    @BeforeEach
    void setUp() {
        product = new Product();
        product.setId(1);
        product.setName("Widget");
        product.setPrice(new BigDecimal("10.00"));
        product.setStockQuantity(5);
        product.setStockThreshold(2);
    }

    @Test
    void stockInIncrementsAndWritesLedger() {
        when(productRepository.findByIdForUpdate(1)).thenReturn(Optional.of(product));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> {
            StockTransaction t = inv.getArgument(0);
            t.setId(99);
            return t;
        });

        StockTransactionResponse response = inventoryService.stockIn(1, 3, "Manual restock");

        assertEquals(8, product.getStockQuantity());
        assertEquals(3, response.quantityChange());
        assertEquals("in", response.transactionType());
        ArgumentCaptor<StockTransaction> captor = ArgumentCaptor.forClass(StockTransaction.class);
        verify(stockTransactionRepository).save(captor.capture());
        assertEquals(TransactionType.in, captor.getValue().getTransactionType());
    }

    @Test
    void stockOutRejectsInsufficientStock() {
        when(productRepository.findByIdForUpdate(1)).thenReturn(Optional.of(product));

        ApiException ex = assertThrows(ApiException.class,
                () -> inventoryService.stockOut(1, 10, "Sale"));

        assertEquals(400, ex.getStatus());
        assertTrue(ex.getDetail().contains("Insufficient stock"));
        assertEquals(5, product.getStockQuantity());
    }

    @Test
    void stockOutDecrementsAndWritesNegativeChange() {
        when(productRepository.findByIdForUpdate(1)).thenReturn(Optional.of(product));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> {
            StockTransaction t = inv.getArgument(0);
            t.setId(100);
            return t;
        });

        StockTransactionResponse response = inventoryService.stockOut(1, 2, "Sale");

        assertEquals(3, product.getStockQuantity());
        assertEquals(-2, response.quantityChange());
        assertEquals("out", response.transactionType());
    }

    @Test
    void stockInRejectsNonPositiveQuantity() {
        ApiException ex = assertThrows(ApiException.class,
                () -> inventoryService.stockIn(1, 0, "x"));
        assertEquals(400, ex.getStatus());
        assertEquals("Stock quantity must be positive", ex.getDetail());
    }

    @Test
    void stockInFailsWhenProductMissing() {
        when(productRepository.findByIdForUpdate(42)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class,
                () -> inventoryService.stockIn(42, 1, "x"));
        assertEquals(404, ex.getStatus());
    }
}
