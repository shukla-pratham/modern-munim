package com.modernmunim.dto;

public record TokenResponse(
        String accessToken,
        String tokenType
) {
    public static TokenResponse bearer(String token) {
        return new TokenResponse(token, "bearer");
    }
}
