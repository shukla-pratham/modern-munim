package com.modernmunim.service;

import com.modernmunim.dto.ExpenseCreateRequest;
import com.modernmunim.dto.ExpenseResponse;
import com.modernmunim.dto.ExpenseUpdateRequest;
import com.modernmunim.entity.Expense;
import com.modernmunim.entity.ExpenseCategory;
import com.modernmunim.entity.ExpenseType;
import com.modernmunim.entity.Product;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.ExpenseRepository;
import com.modernmunim.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ExpenseServiceTest {

    @Mock
    private ExpenseRepository expenseRepository;
    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private ExpenseService expenseService;

    private Expense expense;
    private Product product;

    @BeforeEach
    void setUp() {
        product = new Product();
        product.setId(10);
        product.setName("Widget");
        product.setPrice(new BigDecimal("5.00"));
        product.setStockQuantity(3);

        expense = new Expense();
        expense.setId(1);
        expense.setCategory(ExpenseCategory.OPERATIONS);
        expense.setDescription("Rent");
        expense.setAmount(new BigDecimal("100.00"));
        expense.setExpenseType(ExpenseType.RECURRING);
        expense.setProductId(null);
        expense.setCreatedAt(OffsetDateTime.parse("2026-08-01T10:00:00Z"));
    }

    @Test
    void createPersistsFieldsAndDefaultsExpenseType() {
        when(expenseRepository.save(any())).thenAnswer(inv -> {
            Expense e = inv.getArgument(0);
            e.setId(42);
            e.setCreatedAt(OffsetDateTime.parse("2026-08-11T12:00:00Z"));
            return e;
        });
        when(expenseRepository.findByIdWithProduct(42)).thenAnswer(inv -> {
            Expense e = new Expense();
            e.setId(42);
            e.setCategory(ExpenseCategory.MARKETING);
            e.setDescription("Ads");
            e.setAmount(new BigDecimal("50.00"));
            e.setExpenseType(ExpenseType.ONE_TIME);
            e.setCreatedAt(OffsetDateTime.parse("2026-08-11T12:00:00Z"));
            return Optional.of(e);
        });

        ExpenseResponse response = expenseService.create(
                new ExpenseCreateRequest("marketing", "Ads", new BigDecimal("50.00"), null, null));

        assertEquals(42, response.id());
        assertEquals("marketing", response.category());
        assertEquals("Ads", response.description());
        assertEquals(new BigDecimal("50.00"), response.amount());
        assertEquals("one_time", response.expenseType());
        assertNull(response.productId());

        ArgumentCaptor<Expense> captor = ArgumentCaptor.forClass(Expense.class);
        verify(expenseRepository).save(captor.capture());
        assertEquals(ExpenseCategory.MARKETING, captor.getValue().getCategory());
        assertEquals(ExpenseType.ONE_TIME, captor.getValue().getExpenseType());
    }

    @Test
    void createWithProductIncludesProductName() {
        when(productRepository.findById(10)).thenReturn(Optional.of(product));
        when(expenseRepository.save(any())).thenAnswer(inv -> {
            Expense e = inv.getArgument(0);
            e.setId(5);
            return e;
        });
        when(expenseRepository.findByIdWithProduct(5)).thenAnswer(inv -> {
            Expense e = new Expense();
            e.setId(5);
            e.setCategory(ExpenseCategory.INVENTORY);
            e.setDescription("Restock fee");
            e.setAmount(new BigDecimal("12.00"));
            e.setExpenseType(ExpenseType.ONE_TIME);
            e.setProductId(10);
            e.setProduct(product);
            return Optional.of(e);
        });

        ExpenseResponse response = expenseService.create(
                new ExpenseCreateRequest("inventory", "Restock fee", new BigDecimal("12.00"), "one_time", 10));

        assertEquals(10, response.productId());
        assertEquals("Widget", response.productName());
    }

    @Test
    void createRejectsInvalidCategory() {
        ApiException ex = assertThrows(ApiException.class, () ->
                expenseService.create(
                        new ExpenseCreateRequest("payroll", "X", new BigDecimal("1.00"), "one_time", null)));
        assertEquals(400, ex.getStatus());
        assertTrue(ex.getDetail().contains("Invalid category"));
        verify(expenseRepository, never()).save(any());
    }

    @Test
    void createRejectsInvalidExpenseType() {
        ApiException ex = assertThrows(ApiException.class, () ->
                expenseService.create(
                        new ExpenseCreateRequest("operations", "X", new BigDecimal("1.00"), "monthly", null)));
        assertEquals(400, ex.getStatus());
        assertTrue(ex.getDetail().contains("Invalid expense_type"));
    }

    @Test
    void listFiltersByCategoryAndAppliesSkipLimit() {
        Expense a = cloneExpense(1, ExpenseCategory.OPERATIONS, "A");
        Expense b = cloneExpense(2, ExpenseCategory.OPERATIONS, "B");
        Expense c = cloneExpense(3, ExpenseCategory.OPERATIONS, "C");
        when(expenseRepository.findAll(any(Specification.class), any(Sort.class)))
                .thenReturn(List.of(a, b, c));

        List<ExpenseResponse> page = expenseService.list(1, 1, "operations", null);

        assertEquals(1, page.size());
        assertEquals("B", page.get(0).description());
    }

    @Test
    void listInvalidCategoryFilterIsIgnored() {
        when(expenseRepository.findAll(any(Specification.class), any(Sort.class)))
                .thenReturn(List.of(expense));

        List<ExpenseResponse> page = expenseService.list(0, 100, "not-a-category", null);

        assertEquals(1, page.size());
        verify(expenseRepository).findAll(any(Specification.class), any(Sort.class));
    }

    @Test
    void getExistingAndMissing() {
        when(expenseRepository.findByIdWithProduct(1)).thenReturn(Optional.of(expense));
        assertEquals("Rent", expenseService.get(1).description());

        when(expenseRepository.findByIdWithProduct(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> expenseService.get(99));
        assertEquals(404, ex.getStatus());
        assertEquals("Expense not found", ex.getDetail());
    }

    @Test
    void updateChangesFields() {
        when(expenseRepository.findByIdWithProduct(1)).thenReturn(Optional.of(expense));
        when(expenseRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ExpenseResponse response = expenseService.update(
                1, new ExpenseUpdateRequest("marketing", "Campaign", new BigDecimal("200.00"), "one_time", null));

        assertEquals("marketing", response.category());
        assertEquals("Campaign", response.description());
        assertEquals(new BigDecimal("200.00"), response.amount());
        assertEquals("one_time", response.expenseType());
    }

    @Test
    void updateMissingThrows404() {
        when(expenseRepository.findByIdWithProduct(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () ->
                expenseService.update(99, new ExpenseUpdateRequest("operations", null, null, null, null)));
        assertEquals(404, ex.getStatus());
    }

    @Test
    void deleteExistingAndMissing() {
        when(expenseRepository.findByIdWithProduct(1)).thenReturn(Optional.of(expense));
        expenseService.delete(1);
        verify(expenseRepository).delete(expense);

        when(expenseRepository.findByIdWithProduct(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> expenseService.delete(99));
        assertEquals(404, ex.getStatus());
    }

    private static Expense cloneExpense(int id, ExpenseCategory category, String description) {
        Expense e = new Expense();
        e.setId(id);
        e.setCategory(category);
        e.setDescription(description);
        e.setAmount(new BigDecimal("1.00"));
        e.setExpenseType(ExpenseType.ONE_TIME);
        e.setCreatedAt(OffsetDateTime.parse("2026-08-01T10:00:00Z"));
        return e;
    }
}
