package com.modernmunim.entity;

/**
 * Java constants stay uppercase. Live PostgreSQL {@code expensetype} labels are also
 * uppercase ({@code ONE_TIME}, {@code RECURRING}). Persistence uses
 * {@link ExpenseTypeConverter}; HTTP uses lowercase {@link #apiValue()} /
 * {@link #fromApi(String)}.
 */
public enum ExpenseType {
    ONE_TIME,
    RECURRING;

    /** FastAPI/JSON wire value. */
    public String apiValue() {
        return name().toLowerCase();
    }

    public static ExpenseType fromApi(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new IllegalArgumentException("expense_type required");
        }
        return ExpenseType.valueOf(raw.trim().toUpperCase());
    }
}
