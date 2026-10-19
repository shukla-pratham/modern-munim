package com.modernmunim.service;

import com.modernmunim.dto.ProductCreateRequest;
import com.modernmunim.dto.ProductResponse;
import com.modernmunim.dto.ProductUpdateRequest;
import com.modernmunim.entity.Product;
import com.modernmunim.exception.DomainExceptions;
import com.modernmunim.mapper.DtoMapper;
import com.modernmunim.repository.ProductRepository;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;

    @Transactional(readOnly = true)
    public List<ProductResponse> listProducts(
            int skip,
            int limit,
            String search,
            BigDecimal minPrice,
            BigDecimal maxPrice,
            boolean inStockOnly
    ) {
        Specification<Product> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (search != null && !search.isBlank()) {
                String pattern = "%" + search.toLowerCase() + "%";
                predicates.add(cb.or(
                        cb.like(cb.lower(root.get("name")), pattern),
                        cb.like(cb.lower(root.get("description")), pattern)
                ));
            }
            if (minPrice != null) {
                predicates.add(cb.ge(root.get("price"), minPrice));
            }
            if (maxPrice != null) {
                predicates.add(cb.le(root.get("price"), maxPrice));
            }
            if (inStockOnly) {
                predicates.add(cb.gt(root.get("stockQuantity"), 0));
            }
            return cb.and(predicates.toArray(Predicate[]::new));
        };

        return productRepository.findAll(spec).stream()
                .skip(Math.max(skip, 0))
                .limit(Math.min(Math.max(limit, 1), 100))
                .map(DtoMapper::toProductResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public ProductResponse getProduct(Integer id) {
        Product product = productRepository.findById(id)
                .orElseThrow(DomainExceptions::productNotFound);
        return DtoMapper.toProductResponse(product);
    }

    @Transactional
    public ProductResponse createProduct(ProductCreateRequest request) {
        Product product = new Product();
        product.setName(request.name());
        product.setDescription(request.description());
        product.setPrice(request.price());
        product.setStockQuantity(request.stockQuantity());
        product.setStockThreshold(request.stockThreshold());
        return DtoMapper.toProductResponse(productRepository.save(product));
    }

    @Transactional
    public ProductResponse updateProduct(Integer id, ProductUpdateRequest request) {
        Product product = productRepository.findById(id)
                .orElseThrow(DomainExceptions::productNotFound);
        if (request.name() != null) {
            product.setName(request.name());
        }
        if (request.description() != null) {
            product.setDescription(request.description());
        }
        if (request.price() != null) {
            product.setPrice(request.price());
        }
        if (request.stockThreshold() != null) {
            product.setStockThreshold(request.stockThreshold());
        }
        return DtoMapper.toProductResponse(productRepository.save(product));
    }

    @Transactional
    public void deleteProduct(Integer id) {
        Product product = productRepository.findById(id)
                .orElseThrow(DomainExceptions::productNotFound);
        productRepository.delete(product);
    }
}
