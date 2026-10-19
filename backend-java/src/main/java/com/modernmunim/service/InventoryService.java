package com.modernmunim.service;

import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.StockTransactionResponse;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.TransactionType;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.StockTransactionRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Mirrors FastAPI inventory_service.py:
 * - positive quantity required
 * - pessimistic lock on product
 * - no negative stock
 * - append stock_transactions ledger row
 */
@Service
@RequiredArgsConstructor
public class InventoryService {

    private static final Logger log = LoggerFactory.getLogger(InventoryService.class);

    private final ProductRepository productRepository;
    private final StockTransactionRepository stockTransactionRepository;

    @Transactional
    public StockTransactionResponse stockIn(Integer productId, int quantity, String reason) {
        if (quantity <= 0) {
            throw DomainExceptions.invalidStock("Stock quantity must be positive");
        }
        Product product = productRepository.findByIdForUpdate(productId)
                .orElseThrow(() -> DomainExceptions.productNotFound(productId));

        int oldStock = product.getStockQuantity();
        int newStock = oldStock + quantity;
        if (newStock < oldStock) {
            throw DomainExceptions.invalidStock("Stock quantity overflow");
        }
        product.setStockQuantity(newStock);

        StockTransaction tx = new StockTransaction();
        tx.setProductId(productId);
        tx.setQuantityChange(quantity);
        tx.setTransactionType(TransactionType.in);
        tx.setReason(reason == null || reason.isBlank() ? "Manual restock" : reason);
        tx.setProduct(product);

        StockTransaction saved = stockTransactionRepository.save(tx);
        log.info("Stock in: product={}, qty={}, newStock={}", productId, quantity, newStock);
        return DtoMapper.toStockTransactionResponse(saved);
    }

    @Transactional
    public StockTransactionResponse stockOut(Integer productId, int quantity, String reason) {
        if (quantity <= 0) {
            throw DomainExceptions.invalidStock("Stock quantity must be positive");
        }
        Product product = productRepository.findByIdForUpdate(productId)
                .orElseThrow(() -> DomainExceptions.productNotFound(productId));

        if (product.getStockQuantity() < quantity) {
            throw DomainExceptions.insufficientStock(
                    product.getName(), product.getStockQuantity(), quantity);
        }

        int oldStock = product.getStockQuantity();
        int newStock = oldStock - quantity;
        if (newStock < 0) {
            throw DomainExceptions.insufficientStock(product.getName(), oldStock, quantity);
        }
        product.setStockQuantity(newStock);

        StockTransaction tx = new StockTransaction();
        tx.setProductId(productId);
        tx.setQuantityChange(-quantity);
        tx.setTransactionType(TransactionType.out);
        tx.setReason(reason == null || reason.isBlank() ? "Sale" : reason);
        tx.setProduct(product);

        StockTransaction saved = stockTransactionRepository.save(tx);
        log.info("Stock out: product={}, qty={}, newStock={}", productId, quantity, newStock);
        return DtoMapper.toStockTransactionResponse(saved);
    }

    @Transactional(readOnly = true)
    public List<StockTransactionResponse> listTransactions(Integer productId, int skip, int limit) {
        int safeLimit = Math.min(Math.max(limit, 1), 100);
        int safeSkip = Math.max(skip, 0);
        return stockTransactionRepository.findFiltered(productId).stream()
                .skip(safeSkip)
                .limit(safeLimit)
                .map(DtoMapper::toStockTransactionResponse)
                .toList();
    }

    @Transactional
    public ProductResponse updateThreshold(Integer productId, int threshold) {
        if (threshold < 0) {
            throw DomainExceptions.invalidStock("Stock threshold must be non-negative");
        }
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> DomainExceptions.productNotFound(productId));
        product.setStockThreshold(threshold);
        return DtoMapper.toProductResponse(productRepository.save(product));
    }
}
