package com.modernmunim.entity;

/**
 * Java constants stay uppercase. Live PostgreSQL {@code expensecategory} labels are also
 * uppercase ({@code INVENTORY}, …). Persistence uses {@link ExpenseCategoryConverter};
 * HTTP uses lowercase {@link #apiValue()} / {@link #fromApi(String)}.
 */
public enum ExpenseCategory {
    INVENTORY,
    OPERATIONS,
    MARKETING;

    /** FastAPI/JSON wire value. */
    public String apiValue() {
        return name().toLowerCase();
    }

    public static ExpenseCategory fromApi(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new IllegalArgumentException("category required");
        }
        return ExpenseCategory.valueOf(raw.trim().toUpperCase());
    }
}
