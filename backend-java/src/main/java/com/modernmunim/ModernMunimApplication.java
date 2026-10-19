package com.modernmunim;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.security.servlet.UserDetailsServiceAutoConfiguration;

@SpringBootApplication(exclude = {UserDetailsServiceAutoConfiguration.class})
public class ModernMunimApplication {

    public static void main(String[] args) {
        SpringApplication.run(ModernMunimApplication.class, args);
    }
}
