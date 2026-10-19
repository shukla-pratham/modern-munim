package com.modernmunim.config;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.util.StringUtils;

import javax.sql.DataSource;
import java.net.URI;
import java.net.URISyntaxException;

/**
 * Supports both JDBC URLs and SQLAlchemy-style postgresql:// URLs from the existing .env.
 * Inactive for H2 / non-Postgres URLs so the test profile keeps Boot auto-config.
 */
@Configuration
public class DataSourceConfig {

    @Bean
    @Primary
    @ConditionalOnExpression("'${spring.datasource.url:}'.contains('postgresql') || '${spring.datasource.url:}'.contains('postgres')")
    public DataSource dataSource(
            @Value("${spring.datasource.url}") String url,
            @Value("${spring.datasource.username:}") String username,
            @Value("${spring.datasource.password:}") String password
    ) {
        ParsedJdbc parsed = normalize(url, username, password);
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(parsed.jdbcUrl());
        if (StringUtils.hasText(parsed.username())) {
            ds.setUsername(parsed.username());
        }
        ds.setPassword(parsed.password() == null ? "" : parsed.password());
        ds.setDriverClassName("org.postgresql.Driver");
        return ds;
    }

    static ParsedJdbc normalize(String url, String username, String password) {
        if (url == null || url.isBlank()) {
            throw new IllegalStateException("DATABASE_URL / spring.datasource.url is required");
        }
        if (url.startsWith("jdbc:")) {
            return new ParsedJdbc(url, username, password);
        }
        String cleaned = url
                .replace("postgresql+psycopg2://", "postgresql://")
                .replace("postgres://", "postgresql://");
        try {
            URI uri = new URI(cleaned);
            String userInfo = uri.getUserInfo();
            String user = username;
            String pass = password;
            if (StringUtils.hasText(userInfo)) {
                String[] parts = userInfo.split(":", 2);
                user = parts[0];
                pass = parts.length > 1 ? parts[1] : "";
            }
            int port = uri.getPort() > 0 ? uri.getPort() : 5432;
            String path = uri.getPath() == null ? "" : uri.getPath();
            String jdbc = "jdbc:postgresql://" + uri.getHost() + ":" + port + path;
            return new ParsedJdbc(jdbc, user, pass);
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("Invalid DATABASE_URL: " + url, e);
        }
    }

    record ParsedJdbc(String jdbcUrl, String username, String password) {}
}
