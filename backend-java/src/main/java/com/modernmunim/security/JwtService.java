package com.modernmunim.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

/**
 * JWT compatible with FastAPI python-jose tokens:
 * payload {"sub": "<userId>", "exp": ...}, HS256, shared SECRET_KEY.
 */
@Component
public class JwtService {

    private final SecretKey key;
    private final long expireMinutes;

    public JwtService(
            @Value("${app.security.jwt-secret}") String secret,
            @Value("${app.security.access-token-expire-minutes}") long expireMinutes
    ) {
        if (secret == null || secret.length() < 32) {
            throw new IllegalStateException("SECRET_KEY must be at least 32 characters");
        }
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expireMinutes = expireMinutes;
    }

    public String createToken(Integer userId) {
        Instant now = Instant.now();
        Instant exp = now.plusSeconds(expireMinutes * 60);
        return Jwts.builder()
                .subject(String.valueOf(userId))
                .issuedAt(Date.from(now))
                .expiration(Date.from(exp))
                .signWith(key)
                .compact();
    }

    public Integer parseUserId(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return Integer.valueOf(claims.getSubject());
    }
}
