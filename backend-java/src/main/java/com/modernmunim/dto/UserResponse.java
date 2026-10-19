package com.modernmunim.dto;

import java.time.OffsetDateTime;

public record UserResponse(
        Integer id,
        String email,
        String role,
        OffsetDateTime createdAt
) {}
