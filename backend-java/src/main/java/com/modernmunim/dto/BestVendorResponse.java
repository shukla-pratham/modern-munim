package com.modernmunim.dto;

import java.util.List;

public record BestVendorResponse(
        VendorRankingResponse recommendedVendor,
        List<VendorRankingResponse> alternatives,
        String reasoning
) {}
