package com.modernmunim.exception;

public class ApiException extends RuntimeException {
    private final int status;
    private final String detail;

    public ApiException(int status, String detail) {
        super(detail);
        this.status = status;
        this.detail = detail;
    }

    public int getStatus() {
        return status;
    }

    public String getDetail() {
        return detail;
    }
}
