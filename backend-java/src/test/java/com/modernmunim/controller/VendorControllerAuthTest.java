package com.modernmunim.controller;

import com.modernmunim.dto.VendorCreateResponse;
import com.modernmunim.dto.VendorProductResponse;
import com.modernmunim.dto.VendorRankingResponse;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtAuthenticationFilter;
import com.modernmunim.security.JwtService;
import com.modernmunim.security.SecurityConfig;
import com.modernmunim.security.SecurityErrorHandlers;
import com.modernmunim.service.VendorService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = VendorController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityErrorHandlers.class})
class VendorControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private VendorService vendorService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    private static VendorRankingResponse ranking() {
        return new VendorRankingResponse(
                1, "Acme", new BigDecimal("85.00"), new BigDecimal("90.00"),
                new BigDecimal("80.00"), 5, true, "Rank #1. Overall score: 85.0/100");
    }

    private static VendorCreateResponse created() {
        return new VendorCreateResponse(
                1, "Acme", true, 5, new BigDecimal("90.00"),
                new BigDecimal("80.00"), new BigDecimal("85.00"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanListRankings() throws Exception {
        when(vendorService.rankings(isNull(), isNull(), isNull())).thenReturn(List.of(ranking()));
        mockMvc.perform(get("/api/vendors/rankings")).andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanCreate() throws Exception {
        when(vendorService.create(any())).thenReturn(created());
        mockMvc.perform(post("/api/vendors")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Acme\"}"))
                .andExpect(status().isCreated());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanGetVendorProducts() throws Exception {
        when(vendorService.listVendorProducts(1)).thenReturn(List.of(
                new VendorProductResponse(1, 10, "Widget", new BigDecimal("4.50"), 1, 3)));
        mockMvc.perform(get("/api/vendors/1/products")).andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanAddProduct() throws Exception {
        when(vendorService.addProduct(anyInt(), any())).thenReturn(
                new VendorProductResponse(1, 10, "Widget", new BigDecimal("4.50"), 1, 3));
        mockMvc.perform(post("/api/vendors/1/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"product_id\":10,\"unit_cost\":4.50}"))
                .andExpect(status().isCreated());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanDelete() throws Exception {
        doNothing().when(vendorService).delete(1);
        mockMvc.perform(delete("/api/vendors/1")).andExpect(status().isNoContent());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void createValidationFailure() throws Exception {
        mockMvc.perform(post("/api/vendors")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"\"}"))
                .andExpect(status().isUnprocessableEntity());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotListRankings() throws Exception {
        mockMvc.perform(get("/api/vendors/rankings")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotCreate() throws Exception {
        mockMvc.perform(post("/api/vendors")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Acme\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotDelete() throws Exception {
        mockMvc.perform(delete("/api/vendors/1")).andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedCannotListRankings() throws Exception {
        mockMvc.perform(get("/api/vendors/rankings")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedCannotCreate() throws Exception {
        mockMvc.perform(post("/api/vendors")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Acme\"}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanReadScorecardAndPerformance() throws Exception {
        mockMvc.perform(get("/api/vendors/1/scorecard")).andExpect(status().isOk());
        mockMvc.perform(get("/api/vendors/1/performance")).andExpect(status().isOk());
        mockMvc.perform(get("/api/vendors/best-for-product/10")).andExpect(status().isOk());
        mockMvc.perform(get("/api/vendors/compare-for-product/10")).andExpect(status().isOk());
    }
}
