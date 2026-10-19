package com.modernmunim.service;

import com.modernmunim.dto.OrderCreateRequest;
import com.modernmunim.dto.OrderItemCreateRequest;
import com.modernmunim.dto.OrderResponse;
import com.modernmunim.entity.Order;
import com.modernmunim.entity.OrderStatus;
import com.modernmunim.entity.Product;
import com.modernmunim.entity.StockTransaction;
import com.modernmunim.entity.TransactionType;
import com.modernmunim.entity.User;
import com.modernmunim.entity.UserRole;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.OrderRepository;
import com.modernmunim.repository.ProductRepository;
import com.modernmunim.repository.StockTransactionRepository;
import com.modernmunim.security.UserPrincipal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;
    @Mock
    private ProductRepository productRepository;
    @Mock
    private StockTransactionRepository stockTransactionRepository;

    @InjectMocks
    private OrderService orderService;

    private Product product;

    @BeforeEach
    void setUp() {
        product = new Product();
        product.setId(10);
        product.setName("Widget");
        product.setPrice(new BigDecimal("5.00"));
        product.setStockQuantity(20);
        product.setStockThreshold(2);
    }

    private UserPrincipal principal(int id, UserRole role) {
        User user = new User();
        user.setId(id);
        user.setEmail(role.name() + id + "@example.com");
        user.setPasswordHash("hash");
        user.setRole(role);
        return new UserPrincipal(user);
    }

    @Test
    void createOrderSuccessWritesCompletedOrderAndLedger() {
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(product));
        AtomicInteger orderId = new AtomicInteger();
        when(orderRepository.saveAndFlush(any(Order.class))).thenAnswer(inv -> {
            Order o = inv.getArgument(0);
            o.setId(100);
            orderId.set(100);
            return o;
        });
        when(orderRepository.save(any(Order.class))).thenAnswer(inv -> inv.getArgument(0));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        OrderResponse response = orderService.createOrder(
                4,
                new OrderCreateRequest(List.of(new OrderItemCreateRequest(10, 3)))
        );

        assertEquals(100, response.id());
        assertEquals(4, response.userId());
        assertEquals("completed", response.status());
        assertEquals(new BigDecimal("15.00"), response.totalAmount());
        assertEquals(1, response.items().size());
        assertEquals(17, product.getStockQuantity());

        ArgumentCaptor<StockTransaction> txCaptor = ArgumentCaptor.forClass(StockTransaction.class);
        verify(stockTransactionRepository).save(txCaptor.capture());
        StockTransaction tx = txCaptor.getValue();
        assertEquals(TransactionType.out, tx.getTransactionType());
        assertEquals(-3, tx.getQuantityChange());
        assertEquals("Order #100", tx.getReason());
        assertEquals(OrderStatus.completed, OrderStatus.valueOf(response.status()));
    }

    @Test
    void duplicateProductLinesDeductTotalQuantityAndWriteTwoLedgerRows() {
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(product));
        when(orderRepository.saveAndFlush(any(Order.class))).thenAnswer(inv -> {
            Order o = inv.getArgument(0);
            o.setId(50);
            return o;
        });
        when(orderRepository.save(any(Order.class))).thenAnswer(inv -> inv.getArgument(0));
        when(stockTransactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        orderService.createOrder(
                4,
                new OrderCreateRequest(List.of(
                        new OrderItemCreateRequest(10, 2),
                        new OrderItemCreateRequest(10, 3)
                ))
        );

        assertEquals(15, product.getStockQuantity()); // 20 - 5
        verify(stockTransactionRepository, times(2)).save(any());
        ArgumentCaptor<StockTransaction> captor = ArgumentCaptor.forClass(StockTransaction.class);
        verify(stockTransactionRepository, times(2)).save(captor.capture());
        assertEquals(-2, captor.getAllValues().get(0).getQuantityChange());
        assertEquals(-3, captor.getAllValues().get(1).getQuantityChange());
        assertTrue(captor.getAllValues().stream().allMatch(t -> "Order #50".equals(t.getReason())));
    }

    @Test
    void insufficientStockDoesNotPersistOrder() {
        product.setStockQuantity(1);
        when(productRepository.findByIdForUpdate(10)).thenReturn(Optional.of(product));

        ApiException ex = assertThrows(ApiException.class, () ->
                orderService.createOrder(
                        4,
                        new OrderCreateRequest(List.of(new OrderItemCreateRequest(10, 5)))
                ));

        assertEquals(400, ex.getStatus());
        assertEquals(1, product.getStockQuantity());
        verify(orderRepository, never()).saveAndFlush(any());
        verify(stockTransactionRepository, never()).save(any());
    }

    @Test
    void emptyOrderRejected() {
        ApiException ex = assertThrows(ApiException.class, () ->
                orderService.createOrder(4, new OrderCreateRequest(List.of())));
        assertEquals(422, ex.getStatus());
        verify(orderRepository, never()).saveAndFlush(any());
    }

    @Test
    void invalidQuantityRejected() {
        ApiException ex = assertThrows(ApiException.class, () ->
                orderService.createOrder(
                        4,
                        new OrderCreateRequest(List.of(new OrderItemCreateRequest(10, 0)))
                ));
        assertEquals(422, ex.getStatus());
        verify(productRepository, never()).findByIdForUpdate(any());
    }

    @Test
    void missingProductFailsWithoutPersisting() {
        when(productRepository.findByIdForUpdate(99)).thenReturn(Optional.empty());

        ApiException ex = assertThrows(ApiException.class, () ->
                orderService.createOrder(
                        4,
                        new OrderCreateRequest(List.of(new OrderItemCreateRequest(99, 1)))
                ));
        assertEquals(404, ex.getStatus());
        verify(orderRepository, never()).saveAndFlush(any());
        verify(stockTransactionRepository, never()).save(any());
    }

    @Test
    void ownerCanRetrieveOwnOrder() {
        Order order = new Order();
        order.setId(7);
        order.setUserId(4);
        order.setTotalAmount(new BigDecimal("10.00"));
        order.setStatus(OrderStatus.completed);
        when(orderRepository.findById(7)).thenReturn(Optional.of(order));

        OrderResponse response = orderService.getOrder(7, principal(4, UserRole.customer));
        assertEquals(7, response.id());
    }

    @Test
    void customerCannotRetrieveAnotherUsersOrder() {
        Order order = new Order();
        order.setId(7);
        order.setUserId(4);
        order.setTotalAmount(new BigDecimal("10.00"));
        order.setStatus(OrderStatus.completed);
        when(orderRepository.findById(7)).thenReturn(Optional.of(order));

        ApiException ex = assertThrows(ApiException.class, () ->
                orderService.getOrder(7, principal(9, UserRole.customer)));
        assertEquals(403, ex.getStatus());
    }

    @Test
    void adminCanRetrieveAnyOrder() {
        Order order = new Order();
        order.setId(7);
        order.setUserId(4);
        order.setTotalAmount(new BigDecimal("10.00"));
        order.setStatus(OrderStatus.completed);
        when(orderRepository.findById(7)).thenReturn(Optional.of(order));

        OrderResponse response = orderService.getOrder(7, principal(1, UserRole.admin));
        assertEquals(7, response.id());
    }

    @Test
    void adminListAllOrders() {
        Order order = new Order();
        order.setId(1);
        order.setUserId(4);
        order.setTotalAmount(new BigDecimal("1.00"));
        order.setStatus(OrderStatus.completed);
        when(orderRepository.findAllByOrderByCreatedAtDesc()).thenReturn(List.of(order));

        List<OrderResponse> list = orderService.listAllOrders();
        assertEquals(1, list.size());
        assertEquals(1, list.getFirst().id());
    }
}
