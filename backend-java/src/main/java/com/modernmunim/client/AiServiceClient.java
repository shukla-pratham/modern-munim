package com.modernmunim.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * Boundary client for the Python AI/ML service.
 * Sprint #1: scaffolding only — does not replace FastAPI AI routes yet.
 *
 * Intended flow:
 * Spring Boot → HTTP → Python AI service → ML computation → result → Spring → PostgreSQL
 */
@Component
public class AiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);

    private final RestClient restClient;

    public AiServiceClient(@Value("${app.ai.base-url}") String baseUrl) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
    }

    public String pingHealth() {
        try {
            return restClient.get().uri("/health").retrieve().body(String.class);
        } catch (Exception ex) {
            log.warn("AI service unreachable at configured base URL: {}", ex.getMessage());
            return null;
        }
    }
}
