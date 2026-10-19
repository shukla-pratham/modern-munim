package com.modernmunim.controller;

import com.modernmunim.dto.ExpenseResponse;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtAuthenticationFilter;
import com.modernmunim.security.JwtService;
import com.modernmunim.security.SecurityConfig;
import com.modernmunim.security.SecurityErrorHandlers;
import com.modernmunim.service.ExpenseService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = ExpenseController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, SecurityErrorHandlers.class})
class ExpenseControllerAuthTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ExpenseService expenseService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    private static ExpenseResponse sample() {
        return new ExpenseResponse(
                1,
                "operations",
                "Rent",
                new BigDecimal("100.00"),
                "recurring",
                null,
                null,
                OffsetDateTime.parse("2026-08-01T00:00:00Z")
        );
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanList() throws Exception {
        when(expenseService.list(anyInt(), anyInt(), isNull(), isNull())).thenReturn(List.of(sample()));
        mockMvc.perform(get("/api/expenses"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].category").value("operations"))
                .andExpect(jsonPath("$[0].expense_type").value("recurring"))
                .andExpect(jsonPath("$[0].product_id").doesNotExist());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanCreate() throws Exception {
        when(expenseService.create(any())).thenReturn(sample());
        mockMvc.perform(post("/api/expenses")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"category":"operations","description":"Rent","amount":100.00}
                                """))
                .andExpect(status().isCreated());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void listPassesSnakeCaseProductId() throws Exception {
        when(expenseService.list(0, 100, null, 7)).thenReturn(List.of());
        mockMvc.perform(get("/api/expenses").param("product_id", "7")).andExpect(status().isOk());
        verify(expenseService).list(0, 100, null, 7);
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminPutAcceptsLowercaseEnums() throws Exception {
        when(expenseService.update(any(), any())).thenReturn(sample());
        mockMvc.perform(put("/api/expenses/1")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"category":"operations","description":"Rent","amount":100.00,"expense_type":"recurring"}
                                """))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotList() throws Exception {
        mockMvc.perform(get("/api/expenses")).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void customerCannotDelete() throws Exception {
        mockMvc.perform(delete("/api/expenses/1")).andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedCannotList() throws Exception {
        mockMvc.perform(get("/api/expenses")).andExpect(status().isUnauthorized());
    }

    @Test
    void unauthenticatedCannotPost() throws Exception {
        mockMvc.perform(post("/api/expenses")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"category":"operations","description":"Rent","amount":100.00}
                                """))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminDeleteIsNoContent() throws Exception {
        mockMvc.perform(delete("/api/expenses/1")).andExpect(status().isNoContent());
        verify(expenseService).delete(1);
    }
}
