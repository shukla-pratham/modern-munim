package com.modernmunim.exception;

public final class DomainExceptions {

    private DomainExceptions() {}

    public static ApiException productNotFound(Integer id) {
        return new ApiException(404, id == null ? "Product not found" : "Product " + id + " not found");
    }

    public static ApiException productNotFound() {
        return new ApiException(404, "Product not found");
    }

    public static ApiException insufficientStock(String productName, int available, int requested) {
        return new ApiException(400,
                "Insufficient stock for product '" + productName
                        + "'. Available: " + available + ", Requested: " + requested);
    }

    public static ApiException invalidStock(String detail) {
        return new ApiException(400, detail);
    }

    public static ApiException emailTaken() {
        return new ApiException(400, "Email already registered");
    }

    public static ApiException badCredentials() {
        return new ApiException(401, "Incorrect email or password");
    }

    public static ApiException validation(String detail) {
        return new ApiException(422, detail);
    }

    public static ApiException orderNotFound() {
        return new ApiException(404, "Order not found");
    }

    public static ApiException purchaseOrderNotFound(Integer id) {
        return new ApiException(404,
                id == null ? "Purchase order not found" : "Purchase order " + id + " not found");
    }

    /** FastAPI create_po empty-items HTTPException. */
    public static ApiException purchaseOrderItemsRequired() {
        return new ApiException(400, "At least one item is required");
    }

    public static ApiException expenseNotFound() {
        return new ApiException(404, "Expense not found");
    }

    public static ApiException invalidExpenseCategory(String allowed) {
        return new ApiException(400, "Invalid category. Must be one of: " + allowed);
    }

    public static ApiException invalidExpenseType(String allowed) {
        return new ApiException(400, "Invalid expense_type. Must be one of: " + allowed);
    }

    public static ApiException forbidden(String detail) {
        return new ApiException(403, detail);
    }

    public static ApiException vendorNotFound() {
        return new ApiException(404, "Vendor not found");
    }

    public static ApiException vendorNameExists() {
        return new ApiException(400, "Vendor with this name already exists");
    }

    public static ApiException vendorHasPurchaseOrders() {
        return new ApiException(400,
                "Cannot delete vendor with existing purchase orders. Remove or reassign POs first.");
    }

    public static ApiException vendorAlreadySuppliesProduct() {
        return new ApiException(400, "Vendor already supplies this product");
    }

    public static ApiException noActiveVendorsSupplyProduct() {
        return new ApiException(404, "No active vendors supply this product");
    }
}
