package com.modernmunim.entity;

/**
 * Java / API wire values match FastAPI ({@code in}/{@code out}).
 * Live PostgreSQL {@code transactiontype} labels are {@code STOCK_IN}/{@code STOCK_OUT}.
 * Persistence uses {@link TransactionTypeConverter}.
 */
public enum TransactionType {
    in,
    out
}
