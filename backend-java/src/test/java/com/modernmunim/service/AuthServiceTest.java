package com.modernmunim.service;

import com.modernmunim.dto.RegisterRequest;
import com.modernmunim.dto.UserResponse;
import com.modernmunim.entity.User;
import com.modernmunim.entity.UserRole;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;
    @Mock
    private PasswordEncoder passwordEncoder;
    @Mock
    private JwtService jwtService;

    @InjectMocks
    private AuthService authService;

    @BeforeEach
    void setToken() {
        ReflectionTestUtils.setField(authService, "bootstrapAdminToken", "boot-secret");
    }

    @Test
    void registerAlwaysCreatesCustomer() {
        when(userRepository.existsByEmail("a@b.com")).thenReturn(false);
        when(passwordEncoder.encode("password1")).thenReturn("hash");
        when(userRepository.save(any())).thenAnswer(inv -> {
            User u = inv.getArgument(0);
            u.setId(1);
            return u;
        });

        UserResponse response = authService.register(new RegisterRequest("a@b.com", "password1"));

        assertEquals("customer", response.role());
        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(captor.capture());
        assertEquals(UserRole.customer, captor.getValue().getRole());
    }

    @Test
    void bootstrapAdminRequiresTokenAndNoExistingAdmin() {
        when(userRepository.findAll()).thenReturn(List.of());
        when(userRepository.existsByEmail("admin@mm.com")).thenReturn(false);
        when(passwordEncoder.encode("password1")).thenReturn("hash");
        when(userRepository.save(any())).thenAnswer(inv -> {
            User u = inv.getArgument(0);
            u.setId(2);
            return u;
        });

        UserResponse response = authService.bootstrapAdmin(
                "boot-secret", new RegisterRequest("admin@mm.com", "password1"));

        assertEquals("admin", response.role());
    }

    @Test
    void bootstrapAdminRejectsBadToken() {
        ApiException ex = assertThrows(ApiException.class, () ->
                authService.bootstrapAdmin("wrong", new RegisterRequest("admin@mm.com", "password1")));
        assertEquals(403, ex.getStatus());
    }
}
