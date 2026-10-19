package com.modernmunim.service;

import com.modernmunim.dto.RegisterRequest;
import com.modernmunim.dto.TokenResponse;
import com.modernmunim.dto.UserResponse;
import com.modernmunim.entity.User;
import com.modernmunim.entity.UserRole;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.UserRepository;
import com.modernmunim.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    @Value("${app.security.bootstrap-admin-token:}")
    private String bootstrapAdminToken;

    /**
     * Public registration always creates CUSTOMER.
     * Unlike FastAPI, role escalation via request body is intentionally rejected.
     */
    @Transactional
    public UserResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw DomainExceptions.emailTaken();
        }
        User user = new User();
        user.setEmail(request.email().trim().toLowerCase());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(UserRole.customer);
        return DtoMapper.toUserResponse(userRepository.save(user));
    }

    /**
     * Safer admin provisioning: only when no admin exists AND a bootstrap token matches.
     */
    @Transactional
    public UserResponse bootstrapAdmin(String token, RegisterRequest request) {
        if (!StringUtils.hasText(bootstrapAdminToken) || !bootstrapAdminToken.equals(token)) {
            throw new com.modernmunim.exception.ApiException(403, "Invalid bootstrap token");
        }
        boolean adminExists = userRepository.findAll().stream()
                .anyMatch(u -> u.getRole() == UserRole.admin);
        if (adminExists) {
            throw new com.modernmunim.exception.ApiException(400, "Admin already exists; bootstrap disabled");
        }
        if (userRepository.existsByEmail(request.email())) {
            throw DomainExceptions.emailTaken();
        }
        User user = new User();
        user.setEmail(request.email().trim().toLowerCase());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setRole(UserRole.admin);
        return DtoMapper.toUserResponse(userRepository.save(user));
    }

    @Transactional(readOnly = true)
    public TokenResponse login(String email, String password) {
        User user = userRepository.findByEmail(email.trim().toLowerCase())
                .orElseThrow(DomainExceptions::badCredentials);
        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw DomainExceptions.badCredentials();
        }
        return TokenResponse.bearer(jwtService.createToken(user.getId()));
    }

    @Transactional(readOnly = true)
    public UserResponse me(Integer userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(DomainExceptions::badCredentials);
        return DtoMapper.toUserResponse(user);
    }
}
