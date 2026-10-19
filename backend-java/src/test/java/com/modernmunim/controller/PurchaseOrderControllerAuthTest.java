package com.modernmunim.controller;

import com.modernmunim.dto.PurchaseOrderResponse;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtAuthenticationFilter;
import com.modernmunim.security.JwtService;
import com.modernmunim.security.SecurityConfig;
import com.modernmunim.security.SecurityErrorHandlers;
import com.modernmunim.service.PurchaseOrderService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = PurchaseOrderController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityErrorHandlers.class})
class PurchaseOrderControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PurchaseOrderService purchaseOrderService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    private static PurchaseOrderResponse sampleResponse() {
        return new PurchaseOrderResponse(
                1,
                1,
                "Vendor",
                "PO-AUTH-1",
                "delivered",
                new BigDecimal("10.00"),
                OffsetDateTime.parse("2026-08-01T00:00:00Z"),
                null,
                OffsetDateTime.parse("2026-08-10T00:00:00Z"),
                0,
                List.of()
        );
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanDeliver() throws Exception {
        when(purchaseOrderService.deliver(eq(1), any())).thenReturn(sampleResponse());

        mockMvc.perform(post("/api/purchase-orders/1/deliver"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotDeliver() throws Exception {
        mockMvc.perform(post("/api/purchase-orders/1/deliver"))
                .andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedCannotList() throws Exception {
        mockMvc.perform(get("/api/purchase-orders")).andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotListOrCreate() throws Exception {
        mockMvc.perform(get("/api/purchase-orders")).andExpect(status().isForbidden());
        mockMvc.perform(post("/api/purchase-orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"vendor_id":1,"items":[{"product_id":1,"quantity":1,"unit_cost":1.00}]}
                                """))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanList() throws Exception {
        when(purchaseOrderService.list(null)).thenReturn(List.of(sampleResponse()));
        mockMvc.perform(get("/api/purchase-orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].po_number").value("PO-AUTH-1"))
                .andExpect(jsonPath("$[0].status").value("delivered"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanCreate() throws Exception {
        when(purchaseOrderService.create(any())).thenReturn(sampleResponse());
        mockMvc.perform(post("/api/purchase-orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"vendor_id":1,"items":[{"product_id":10,"quantity":3,"unit_cost":4.00}]}
                                """))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void listPassesVendorId() throws Exception {
        when(purchaseOrderService.list(7)).thenReturn(List.of());
        mockMvc.perform(get("/api/purchase-orders").param("vendor_id", "7")).andExpect(status().isOk());
        verify(purchaseOrderService).list(7);
    }
}
