package com.modernmunim.service;

import com.modernmunim.dto.ExpenseCreateRequest;
import com.modernmunim.dto.ExpenseResponse;
import com.modernmunim.dto.ExpenseUpdateRequest;
import com.modernmunim.entity.Expense;
import com.modernmunim.entity.ExpenseCategory;
import com.modernmunim.entity.ExpenseType;
import com.modernmunim.entity.Product;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.ExpenseRepository;
import com.modernmunim.repository.ProductRepository;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Mirrors FastAPI expense_service.py — financial CRUD only; does not touch stock/ledger.
 */
@Service
@RequiredArgsConstructor
public class ExpenseService {

    private final ExpenseRepository expenseRepository;
    private final ProductRepository productRepository;

    @Transactional(readOnly = true)
    public List<ExpenseResponse> list(int skip, int limit, String category, Integer productId) {
        ExpenseCategory categoryFilter = parseCategoryFilter(category);
        int safeSkip = Math.max(skip, 0);
        int safeLimit = Math.min(Math.max(limit, 1), 100);

        Specification<Expense> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (categoryFilter != null) {
                predicates.add(cb.equal(root.get("category"), categoryFilter));
            }
            if (productId != null) {
                predicates.add(cb.equal(root.get("productId"), productId));
            }
            return cb.and(predicates.toArray(Predicate[]::new));
        };

        return expenseRepository.findAll(spec, Sort.by(Sort.Direction.DESC, "createdAt")).stream()
                .skip(safeSkip)
                .limit(safeLimit)
                .map(DtoMapper::toExpenseResponse)
                .toList();
    }

    /**
     * Used by update/delete and unit tests. FastAPI exposes get_expense in the service layer
     * but has no GET /{id} HTTP route — Spring matches that (no controller get-by-id).
     */
    @Transactional(readOnly = true)
    public ExpenseResponse get(Integer id) {
        return DtoMapper.toExpenseResponse(requireExpense(id));
    }

    @Transactional
    public ExpenseResponse create(ExpenseCreateRequest request) {
        ExpenseCategory category = parseCategoryRequired(request.category());
        ExpenseType expenseType = parseExpenseTypeRequired(request.expenseType());

        Expense expense = new Expense();
        expense.setCategory(category);
        expense.setDescription(request.description());
        expense.setAmount(request.amount());
        expense.setExpenseType(expenseType);
        expense.setProductId(request.productId());

        attachProductIfPresent(expense);
        Expense saved = expenseRepository.save(expense);
        return DtoMapper.toExpenseResponse(reload(saved.getId()));
    }

    @Transactional
    public ExpenseResponse update(Integer id, ExpenseUpdateRequest request) {
        Expense expense = requireExpense(id);

        if (request.category() != null) {
            expense.setCategory(parseCategoryRequired(request.category()));
        }
        if (request.description() != null) {
            expense.setDescription(request.description());
        }
        if (request.amount() != null) {
            expense.setAmount(request.amount());
        }
        if (request.expenseType() != null) {
            expense.setExpenseType(parseExpenseTypeRequired(request.expenseType()));
        }
        if (request.productId() != null) {
            expense.setProductId(request.productId());
            attachProductIfPresent(expense);
        }

        expenseRepository.save(expense);
        return DtoMapper.toExpenseResponse(reload(id));
    }

    @Transactional
    public void delete(Integer id) {
        Expense expense = requireExpense(id);
        expenseRepository.delete(expense);
    }

    private Expense requireExpense(Integer id) {
        return expenseRepository.findByIdWithProduct(id)
                .orElseThrow(DomainExceptions::expenseNotFound);
    }

    private Expense reload(Integer id) {
        return expenseRepository.findByIdWithProduct(id)
                .orElseThrow(DomainExceptions::expenseNotFound);
    }

    private void attachProductIfPresent(Expense expense) {
        if (expense.getProductId() == null) {
            expense.setProduct(null);
            return;
        }
        Product product = productRepository.findById(expense.getProductId()).orElse(null);
        expense.setProduct(product);
    }

    /** Invalid category filter is silently ignored (FastAPI parity). */
    private static ExpenseCategory parseCategoryFilter(String category) {
        if (category == null || category.isBlank()) {
            return null;
        }
        try {
            return ExpenseCategory.fromApi(category);
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    private static ExpenseCategory parseCategoryRequired(String category) {
        try {
            return ExpenseCategory.fromApi(category);
        } catch (RuntimeException ex) {
            throw DomainExceptions.invalidExpenseCategory(allowedCategories());
        }
    }

    private static ExpenseType parseExpenseTypeRequired(String expenseType) {
        try {
            return ExpenseType.fromApi(expenseType);
        } catch (RuntimeException ex) {
            throw DomainExceptions.invalidExpenseType(allowedExpenseTypes());
        }
    }

    private static String allowedCategories() {
        return Arrays.stream(ExpenseCategory.values())
                .map(e -> "'" + e.apiValue() + "'")
                .collect(Collectors.joining(", ", "[", "]"));
    }

    private static String allowedExpenseTypes() {
        return Arrays.stream(ExpenseType.values())
                .map(e -> "'" + e.apiValue() + "'")
                .collect(Collectors.joining(", ", "[", "]"));
    }
}
