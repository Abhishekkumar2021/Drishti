package com.example.auth;

import java.util.List;

public interface TokenValidator {
    boolean validate(String token);
}

public class AuthService implements TokenValidator {
    private final String issuer;
    private static final int MAX_RETRIES = 3;

    public AuthService(String issuer) {
        this.issuer = issuer;
    }

    @Override
    public boolean validate(String token) {
        return token != null;
    }
}
