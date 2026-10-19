package com.modernmunim.config;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DataSourceConfigTest {

    @Test
    void normalizesSqlAlchemyUrl() {
        DataSourceConfig.ParsedJdbc parsed = DataSourceConfig.normalize(
                "postgresql://alice:secret@localhost:5432/marketplace_db", "", "");
        assertEquals("jdbc:postgresql://localhost:5432/marketplace_db", parsed.jdbcUrl());
        assertEquals("alice", parsed.username());
        assertEquals("secret", parsed.password());
    }

    @Test
    void keepsJdbcUrl() {
        DataSourceConfig.ParsedJdbc parsed = DataSourceConfig.normalize(
                "jdbc:postgresql://localhost:5432/marketplace_db", "u", "p");
        assertEquals("jdbc:postgresql://localhost:5432/marketplace_db", parsed.jdbcUrl());
        assertEquals("u", parsed.username());
        assertEquals("p", parsed.password());
    }
}
