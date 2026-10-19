package com.modernmunim.controller;

import com.modernmunim.exception.GlobalExceptionHandler;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtAuthenticationFilter;
import com.modernmunim.security.JwtService;
import com.modernmunim.security.SecurityConfig;
import com.modernmunim.security.SecurityErrorHandlers;
import com.modernmunim.service.OrderService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = OrderController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityErrorHandlers.class, GlobalExceptionHandler.class})
class OrderControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    @Test
    void unauthenticatedCreateIs401() throws Exception {
        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"items\":[]}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCreateIs403() throws Exception {
        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"items\":[]}"))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerGetByIdIs403() throws Exception {
        mockMvc.perform(get("/api/orders/1")).andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedProductListIs401() throws Exception {
        mockMvc.perform(get("/api/products")).andExpect(status().isUnauthorized());
    }
}
