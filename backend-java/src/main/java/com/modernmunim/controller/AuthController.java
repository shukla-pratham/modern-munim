package com.modernmunim.controller;

import com.modernmunim.dto.RegisterRequest;
import com.modernmunim.dto.TokenResponse;
import com.modernmunim.dto.UserResponse;
import com.modernmunim.security.UserPrincipal;
import com.modernmunim.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Tag(name = "Auth")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Register customer (public). Admin role cannot be self-assigned.")
    public UserResponse register(@Valid @RequestBody RegisterRequest request) {
        return authService.register(request);
    }

    @PostMapping("/bootstrap-admin")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Create the first admin when BOOTSTRAP_ADMIN_TOKEN matches and no admin exists")
    public UserResponse bootstrapAdmin(
            @RequestHeader("X-Bootstrap-Token") String token,
            @Valid @RequestBody RegisterRequest request
    ) {
        return authService.bootstrapAdmin(token, request);
    }

    @PostMapping(value = "/login", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE)
    @Operation(summary = "OAuth2-compatible login (username=email, password)")
    public TokenResponse login(
            @RequestParam("username") String username,
            @RequestParam("password") String password
    ) {
        return authService.login(username, password);
    }

    @GetMapping("/me")
    @Operation(summary = "Current user")
    public UserResponse me(@AuthenticationPrincipal UserPrincipal principal) {
        return authService.me(principal.getId());
    }
}
