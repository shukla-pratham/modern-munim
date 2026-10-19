package com.modernmunim.service;

import com.modernmunim.dto.ProductCreateRequest;
import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.ProductUpdateRequest;
import com.modernmunim.entity.Product;
import com.modernmunim.exception.ApiException;
import com.modernmunim.repository.ProductRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private ProductService productService;

    @Test
    void createProductPersistsDefaults() {
        when(productRepository.save(any())).thenAnswer(inv -> {
            Product p = inv.getArgument(0);
            p.setId(7);
            return p;
        });

        ProductResponse response = productService.createProduct(
                new ProductCreateRequest("SKU-1", "desc", new BigDecimal("12.50"), null, null));

        assertEquals(7, response.id());
        assertEquals(0, response.stockQuantity());
        assertEquals(10, response.stockThreshold());
        ArgumentCaptor<Product> captor = ArgumentCaptor.forClass(Product.class);
        verify(productRepository).save(captor.capture());
        assertEquals("SKU-1", captor.getValue().getName());
    }

    @Test
    void updateDoesNotAllowChangingStockViaProductApi() {
        Product product = new Product();
        product.setId(1);
        product.setName("Old");
        product.setPrice(new BigDecimal("1.00"));
        product.setStockQuantity(9);
        product.setStockThreshold(3);
        when(productRepository.findById(1)).thenReturn(Optional.of(product));
        when(productRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ProductResponse response = productService.updateProduct(
                1, new ProductUpdateRequest("New", null, new BigDecimal("2.00"), 5));

        assertEquals("New", response.name());
        assertEquals(9, response.stockQuantity());
        assertEquals(5, response.stockThreshold());
    }

    @Test
    void getMissingProductThrows404() {
        when(productRepository.findById(99)).thenReturn(Optional.empty());
        ApiException ex = assertThrows(ApiException.class, () -> productService.getProduct(99));
        assertEquals(404, ex.getStatus());
    }
}
