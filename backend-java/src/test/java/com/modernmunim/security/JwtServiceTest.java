package com.modernmunim.security;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class JwtServiceTest {

    @Test
    void roundTripUserId() {
        JwtService jwt = new JwtService("test-secret-key-minimum-32-characters-long!!", 30);
        String token = jwt.createToken(42);
        assertEquals(42, jwt.parseUserId(token));
    }

    @Test
    void rejectsShortSecret() {
        assertThrows(IllegalStateException.class,
                () -> new JwtService("too-short", 30));
    }
}
