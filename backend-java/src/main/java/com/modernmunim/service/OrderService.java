package com.modernmunim.service;

import com.modernmunim.dto.OrderCreateRequest;
import com.modernmunim.dto.OrderItemCreateRequest;
import com.modernmunim.dto.OrderResponse;
import com.modernmunim.entity.Order;
import com.modernmunim.entity.OrderItem;
import com.modernmunim.entity.OrderStatus;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.TransactionType;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.OrderRepository;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.StockTransactionRepository;
import com.modernmunim.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Mirrors FastAPI order_service.create_order with one intentional integrity upgrade:
 * every stock deduction also writes a stock_transactions ledger row (reason = "Order #&lt;id&gt;").
 */
@Service
@RequiredArgsConstructor
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final StockTransactionRepository stockTransactionRepository;

    @Transactional
    public OrderResponse createOrder(Integer userId, OrderCreateRequest request) {
        if (request.items() == null || request.items().isEmpty()) {
            throw DomainExceptions.validation("Order must contain at least one item");
        }

        Map<Integer, Product> lockedProducts = new HashMap<>();

        // Pass 1: validate lines and lock products (same pattern as FastAPI).
        for (OrderItemCreateRequest item : request.items()) {
            if (item.quantity() == null || item.quantity() <= 0) {
                throw DomainExceptions.validation(
                        "Quantity must be positive for product " + item.productId());
            }
            Product product = productRepository.findByIdForUpdate(item.productId())
                    .orElseThrow(() -> DomainExceptions.productNotFound(item.productId()));
            if (product.getStockQuantity() < item.quantity()) {
                throw DomainExceptions.insufficientStock(
                        product.getName(), product.getStockQuantity(), item.quantity());
            }
            lockedProducts.put(product.getId(), product);
        }

        BigDecimal total = BigDecimal.ZERO;
        for (OrderItemCreateRequest item : request.items()) {
            Product product = lockedProducts.get(item.productId());
            total = total.add(product.getPrice().multiply(BigDecimal.valueOf(item.quantity())));
        }

        Order order = new Order();
        order.setUserId(userId);
        order.setTotalAmount(total);
        order.setStatus(OrderStatus.completed);

        // Flush to obtain order id for ledger reason before commit.
        order = orderRepository.saveAndFlush(order);
        String ledgerReason = "Order #" + order.getId();

        // Pass 2: create items, deduct stock, write ledger.
        for (OrderItemCreateRequest itemData : request.items()) {
            Product product = lockedProducts.get(itemData.productId());

            OrderItem orderItem = new OrderItem();
            orderItem.setProductId(product.getId());
            orderItem.setProduct(product);
            orderItem.setQuantity(itemData.quantity());
            orderItem.setPriceAtPurchase(product.getPrice());
            order.addItem(orderItem);

            int previous = product.getStockQuantity();
            int next = previous - itemData.quantity();
            if (next < 0) {
                throw DomainExceptions.insufficientStock(
                        product.getName(), previous, itemData.quantity());
            }
            product.setStockQuantity(next);

            StockTransaction tx = new StockTransaction();
            tx.setProductId(product.getId());
            tx.setProduct(product);
            tx.setQuantityChange(-itemData.quantity());
            tx.setTransactionType(TransactionType.out);
            tx.setReason(ledgerReason);
            stockTransactionRepository.save(tx);
        }

        order = orderRepository.save(order);
        log.info("Order {} created for user {} with {} items (ledger written)",
                order.getId(), userId, order.getItems().size());
        return DtoMapper.toOrderResponse(order);
    }

    @Transactional(readOnly = true)
    public List<OrderResponse> listMyOrders(Integer userId) {
        return orderRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(DtoMapper::toOrderResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<OrderResponse> listAllOrders() {
        return orderRepository.findAllByOrderByCreatedAtDesc().stream()
                .map(DtoMapper::toOrderResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrder(Integer orderId, UserPrincipal principal) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(DomainExceptions::orderNotFound);
        if (!principal.isAdmin() && !order.getUserId().equals(principal.getId())) {
            throw DomainExceptions.forbidden("Not enough permissions");
        }
        return DtoMapper.toOrderResponse(order);
    }
}
