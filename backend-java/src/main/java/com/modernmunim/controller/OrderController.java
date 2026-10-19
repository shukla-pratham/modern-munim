package com.modernmunim.controller;

import com.modernmunim.dto.OrderCreateRequest;
import com.modernmunim.dto.OrderResponse;
import com.modernmunim.security.UserPrincipal;
import com.modernmunim.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
@Tag(name = "Orders")
@SecurityRequirement(name = "bearerAuth")
public class OrderController {

    private final OrderService orderService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create order (admin); status completed; writes stock ledger")
    public OrderResponse create(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody OrderCreateRequest request
    ) {
        return orderService.createOrder(principal.getId(), request);
    }

    @GetMapping
    @Operation(summary = "List all orders (admin)")
    public List<OrderResponse> listAll() {
        return orderService.listAllOrders();
    }

    @GetMapping("/my-orders")
    @Operation(summary = "List current user's orders (admin)")
    public List<OrderResponse> listMine(@AuthenticationPrincipal UserPrincipal principal) {
        return orderService.listMyOrders(principal.getId());
    }

    @GetMapping("/{orderId}")
    @Operation(summary = "Get order by id (admin)")
    public OrderResponse get(
            @PathVariable Integer orderId,
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        return orderService.getOrder(orderId, principal);
    }
}
