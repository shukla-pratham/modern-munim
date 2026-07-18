# Phase 2 - AI/ML Intelligence Layer

## Overview

Phase 2 adds an AI/ML-powered decision intelligence layer on top of Phase 1's stable foundation. All AI features use **batch processing** and **explainable models** to provide actionable business insights.

## Key Design Principles

1. **Batch Processing**: AI runs as background jobs, not real-time inference
2. **Explainability**: Every decision includes human-readable explanations
3. **Profit-Aware**: AI considers margins and costs, not just demand
4. **Free & Open-Source**: Uses only free libraries (Prophet, pandas, scikit-learn)
5. **Separation of Concerns**: ML logic separate from API routes

## Features

### 1. Demand Intelligence

**What it does:**
- Analyzes historical sales data to detect trends (rising/stable/declining)
- Forecasts future demand using Prophet (with statistical fallback)
- Provides confidence scores for all predictions

**How it works:**
- Extracts daily sales data for each product
- Uses Prophet for time-series forecasting (handles seasonality)
- Falls back to moving average + trend if Prophet unavailable
- Stores forecasts in database for fast retrieval

**Usage:**
```python
# Forecasts are generated automatically in batch jobs
# Access via API: GET /api/ai/forecasts?product_id=123
```

### 2. Stockout Prediction

**What it does:**
- Predicts days until stockout based on sales velocity
- Categorizes risk as low/medium/high
- Provides explanations for predictions

**How it works:**
- Calculates average units sold per day (sales velocity)
- Divides current stock by sales velocity
- Adjusts confidence based on data quality

**Example:**
```
Product: Wireless Mouse
Current Stock: 50 units
Sales Velocity: 5 units/day
Prediction: 10 days until stockout (medium risk)
```

### 3. Smart Restocking Recommendations

**What it does:**
- Recommends restock quantity and timing
- Considers demand forecast, stockout risk, margins, and costs
- Provides "yes", "no", or "urgent" recommendations with explanations

**Decision Factors:**
- **Demand Forecast Impact (30%)**: How much forecasted demand influences decision
- **Stock Risk Impact (30%)**: How much stockout risk influences decision
- **Margin Impact (20%)**: How much profit margin influences decision
- **Cost Impact (20%)**: How much holding costs influence decision

**Example Explanation:**
```
"Recommended restock: 100 units within 5 days. 
Forecasted demand: 150 units over 30 days. 
Current stock: 20 units. 
Stockout risk: high. 
Margin: 25.5%."
```

### 4. Dead Stock Detection

**What it does:**
- Identifies products that should be cleared or discontinued
- Calculates risk scores based on multiple factors
- Suggests actions: clearance, discount, stop ordering, or monitor

**Detection Factors:**
- Days since last sale
- Demand trend (declining = higher risk)
- Profit margin (negative = higher risk)
- Holding cost ratio (high relative to revenue = higher risk)

**Risk Scoring:**
- 0-40: No action needed (monitor)
- 40-70: Warning (monitor closely)
- 70-100: Dead stock (take action)

### 5. Explainable AI

**Why Explainability Matters:**
- Business users need to understand AI decisions
- Builds trust in AI recommendations
- Helps identify when AI might be wrong
- Required for regulatory compliance

**What's Explained:**
- **Forecasts**: Why demand is predicted to be X units
- **Stockout Predictions**: Why stockout is predicted in Y days
- **Restocking**: Why restock/not restock, with factor contributions
- **Dead Stock**: Why product is flagged, with risk factors

**Example Explanation Structure:**
```
Decision: Restock 100 units
Reasoning:
- Demand forecast: 150 units needed (high impact)
- Stockout risk: High (7 days until stockout) (high impact)
- Margin: 25% (healthy) (medium impact)
- Holding cost: Low relative to revenue (low impact)
Confidence: 85%
```

### 6. Alerts & Automation

**Alert Types:**
- **Stockout Alerts**: High-risk products predicted to stockout soon
- **Dead Stock Alerts**: Products identified as dead stock
- **Low Margin Alerts**: High-demand products with low margins

**Automation:**
- Batch jobs run on schedule (daily/weekly)
- Alerts generated automatically from predictions
- Stored in database for admin review
- Can be marked as read/unread

## Technical Implementation

### ML Service Layer (`app/services/ml_service.py`)

**Key Functions:**
- `get_sales_time_series()`: Extract daily sales data
- `detect_trend()`: Detect demand trends using linear regression
- `forecast_demand_prophet()`: Forecast using Prophet (with fallback)
- `predict_stockout()`: Predict days until stockout
- `recommend_restocking()`: Generate restocking recommendations
- `detect_dead_stock()`: Detect dead stock products

### Persistence Layer (`app/services/ai_persistence_service.py`)

**Key Functions:**
- `persist_demand_forecasts()`: Save forecasts to database
- `persist_stockout_prediction()`: Save stockout predictions
- `persist_restocking_recommendation()`: Save recommendations
- `persist_dead_stock_detection()`: Save dead stock detections
- `run_ai_batch_processing()`: Run full batch processing

### Background Jobs (`app/jobs/ai_batch_job.py`)

**How to Run:**
```bash
# Manual execution
python -m app.jobs.ai_batch_job

# Scheduled (cron example - daily at 2 AM)
0 2 * * * cd /path/to/backend && python -m app.jobs.ai_batch_job
```

**What it does:**
1. Processes all products (or specified products)
2. Generates forecasts, predictions, recommendations, detections
3. Creates alerts based on predictions
4. Returns summary of processing results

### API Endpoints (`app/api/ai_insights.py`)

**Read-Only Endpoints:**
- `GET /api/ai/forecasts`: Get demand forecasts
- `GET /api/ai/stockout-predictions`: Get stockout predictions
- `GET /api/ai/restocking-recommendations`: Get restocking recommendations
- `GET /api/ai/dead-stock-detections`: Get dead stock detections
- `GET /api/ai/alerts`: Get AI alerts
- `GET /api/ai/products/{id}/insights`: Get all insights for a product

**Action Endpoints:**
- `PUT /api/ai/alerts/{id}/read`: Mark alert as read
- `POST /api/ai/batch-process`: Trigger manual batch processing (admin only)

## Database Schema

### DemandForecast
- Stores forecasted demand for each product/date
- Includes confidence scores and trend information
- Indexed by product_id and forecast_date for fast queries

### StockoutPrediction
- Stores stockout predictions per product
- Includes risk level, days until stockout, sales velocity
- Includes explanation for transparency

### RestockingRecommendation
- Stores restocking recommendations
- Includes recommended quantity, timing, decision factors
- Includes explanation and confidence score

### DeadStockDetection
- Stores dead stock detections
- Includes risk score, suggested action, explanation
- Includes detection factors (trend, margin, etc.)

### AIAlert
- Stores AI-generated alerts
- Includes alert type, severity, product reference
- Includes read/unread status

## Usage Examples

### Running Batch Processing

```python
from app.core.database import SessionLocal
from app.services.ai_persistence_service import run_ai_batch_processing

db = SessionLocal()
summary = run_ai_batch_processing(db)
# Returns: {products_processed, forecasts_created, ...}
```

### Accessing AI Insights

```python
# Get restocking recommendations
GET /api/ai/restocking-recommendations?should_restock=urgent

# Get high-risk stockout predictions
GET /api/ai/stockout-predictions?risk_level=high

# Get all insights for a product
GET /api/ai/products/123/insights
```

## Performance Considerations

- **Batch Processing**: Runs offline, doesn't block API requests
- **Database Indexing**: All AI tables indexed for fast queries
- **Caching**: AI outputs stored in database, no recomputation needed
- **Fallback Logic**: Simple methods used when complex models unavailable

## Future Enhancements (Phase 3+)

- **Price Optimization**: AI-driven pricing recommendations
- **Customer Behavior Analysis**: Segment customers, predict churn
- **Anomaly Detection**: Detect unusual patterns in sales/expenses
- **Automated Actions**: Auto-restock when confidence is high
- **LLM Assistant**: Natural language queries about AI insights (grounded in data)

## Troubleshooting

**Prophet Installation Issues:**
- Prophet requires system dependencies (C++ compiler)
- If unavailable, system falls back to simple statistical methods
- Check logs for fallback messages

**Low Confidence Scores:**
- Usually indicates insufficient historical data
- Need at least 7-14 days of sales data for reliable predictions
- More data = higher confidence

**Incorrect Predictions:**
- Review explanations to understand AI reasoning
- Check if recent events (promotions, seasonality) affected data
- Adjust thresholds or parameters if needed
