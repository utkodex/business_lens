# Business Lens AI - Query Execution Logs

This document contains the execution logs for 20 sample queries processed by the AI pipeline.

## Query 1: What was the total revenue for ColaMax in 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0     1472092.03
```

## Query 2: Compare FizzPop vs ColaMax total revenue for the year 2024.
- **Intent Predicted:** `comparison`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(CASE WHEN dp.brand = 'FizzPop' THEN fis.total_sales ELSE 0 END) AS FizzPop_Revenue,
    SUM(CASE WHEN dp.brand = 'ColaMax' THEN fis.total_sales ELSE 0 END) AS ColaMax_Revenue
FROM 
    fact_internal_sales fis
JOIN 
    dim_product dp ON fis.product_id = dp.product_id
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
WHERE 
    dt.year = 2024
```
- **Execution Result:**
```text
 FizzPop_Revenue  ColaMax_Revenue
      1463567.31       1472092.03
```

## Query 3: What is the total revenue for DoughBoy in 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0      965819.82
```

## Query 4: How does Zap's revenue compare to FizzPop in 2024?
- **Intent Predicted:** `comparison`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
WITH zap_revenue AS (
    SELECT 
        SUM(fis.total_sales) AS total_revenue
    FROM 
        fact_internal_sales fis
    JOIN 
        dim_time dt ON fis.date_id = dt.date_id
    JOIN 
        dim_product dp ON fis.product_id = dp.product_id
    WHERE 
        dp.brand = 'Zap' AND dt.year = 2024
),
fizzpop_revenue AS (
    SELECT 
        SUM(fis.total_sales) AS total_revenue
    FROM 
        fact_internal_sales fis
    JOIN 
        dim_time dt ON fis.date_id = dt.date_id
    JOIN 
        dim_product dp ON fis.product_id = dp.product_id
    WHERE 
        dp.brand = 'FizzPop' AND dt.year = 2024
)
SELECT 
    zap_revenue.total_revenue AS zap_revenue,
    fizzpop_revenue.total_revenue AS fizzpop_revenue,
    (zap_revenue.total_revenue - fizzpop_revenue.total_revenue) / fizzpop_revenue.total_revenue * 100 AS revenue_difference
FROM 
    zap_revenue, fizzpop_revenue;
```
- **Execution Result:**
```text
 zap_revenue  fizzpop_revenue  revenue_difference
   993228.58       1463567.31           -32.13646
```

## Query 5: What was the total sales volume across all categories in 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(fis.total_sales) AS total_sales_volume
FROM 
    fact_internal_sales fis
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
WHERE 
    dt.year = 2024;
```
- **Execution Result:**
```text
 total_sales_volume
         9252521.47
```

## Query 6: Which brand had the highest revenue in the Beverages category in 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    dp.brand, 
    SUM(fis.total_sales) AS total_revenue
FROM 
    fact_internal_sales fis
JOIN 
    dim_product dp ON fis.product_id = dp.product_id
JOIN 
    dim_category dc ON fis.category_id = dc.category_id
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
WHERE 
    dc.category = 'Beverages' 
    AND dt.year = 2024
GROUP BY 
    dp.brand
ORDER BY 
    total_revenue DESC
LIMIT 1;
```
- **Execution Result:**
```text
  brand  total_revenue
ColaMax      1470680.3
```

## Query 7: What is the YoY growth of ColaMax from 2023 to 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
WITH sales_2023 AS (
    SELECT 
        SUM(total_sales) AS total_sales_2023
    FROM 
        fact_internal_sales 
    JOIN 
        dim_time ON fact_internal_sales.date_id = dim_time.date_id
    JOIN 
        dim_product ON fact_internal_sales.product_id = dim_product.product_id
    WHERE 
        dim_product.brand = 'ColaMax' 
        AND dim_time.year = 2023
),
sales_2024 AS (
    SELECT 
        SUM(total_sales) AS total_sales_2024
    FROM 
        fact_internal_sales 
    JOIN 
        dim_time ON fact_internal_sales.date_id = dim_time.date_id
    JOIN 
        dim_product ON fact_internal_sales.product_id = dim_product.product_id
    WHERE 
        dim_product.brand = 'ColaMax' 
        AND dim_time.year = 2024
)
SELECT 
    ((sales_2024.total_sales_2024 - sales_2023.total_sales_2023) / sales_2023.total_sales_2023) * 100 AS yoy_growth
FROM 
    sales_2023, 
    sales_2024;
```
- **Execution Result:**
```text
 yoy_growth
        NaN
```

## Query 8: List all competitor brands in the Snacks category.
- **Intent Predicted:** `comparison`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT DISTINCT T3.brand
FROM fact_competitor_market T1
JOIN dim_category T2 ON T1.category_id = T2.category_id
JOIN dim_product T3 ON T1.retailer_id = T3.product_id
WHERE T2.category = 'Snacks';
```
- **Execution Result:**
```text
     brand
SweetTreat
CrunchBite
       Zap
   FizzPop
  DoughBoy
   ColaMax
```

## Query 9: Which category generated more revenue in 2024: Beverages or Snacks?
- **Intent Predicted:** `comparison`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
WITH category_revenue AS (
    SELECT 
        dc.category,
        SUM(fis.total_sales) AS total_revenue
    FROM 
        fact_internal_sales fis
    JOIN 
        dim_time dt ON fis.date_id = dt.date_id
    JOIN 
        dim_category dc ON fis.category_id = dc.category_id
    WHERE 
        dt.year = 2024
        AND dc.category IN ('Beverages', 'Snacks')
    GROUP BY 
        dc.category
)
SELECT 
    category,
    total_revenue
FROM 
    category_revenue
ORDER BY 
    total_revenue DESC
LIMIT 1;
```
- **Execution Result:**
```text
 category  total_revenue
Beverages     4897527.43
```

## Query 10: What was the revenue for Zap in 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(fis.total_sales) AS total_revenue
FROM 
    fact_internal_sales fis
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
JOIN 
    dim_product dp ON fis.product_id = dp.product_id
WHERE 
    dt.year = 2024 AND dp.brand = 'Zap'
```
- **Execution Result:**
```text
 total_revenue
     993228.58
```

## Query 11: Compare our internal sales volume vs competitor sales volume for Beverages in 2024.
- **Intent Predicted:** `comparison`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(fis.volume) AS internal_sales_volume,
    SUM(fcm.competitor_volume) AS competitor_sales_volume
FROM 
    fact_internal_sales fis
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
JOIN 
    dim_category dc ON fis.category_id = dc.category_id
JOIN 
    fact_competitor_market fcm ON fis.date_id = fcm.date_id AND fis.category_id = fcm.category_id AND fis.retailer_id = fcm.retailer_id
WHERE 
    dt.year = 2024 AND dc.category = 'Beverages'
```
- **Execution Result:**
```text
 internal_sales_volume  competitor_sales_volume
             1301025.0               12557343.0
```

## Query 12: What was the revenue for ColaMax in week 10 of 2024?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(fis.total_sales) AS revenue
FROM 
    fact_internal_sales fis
JOIN 
    dim_product dp ON fis.product_id = dp.product_id
JOIN 
    dim_time dt ON fis.date_id = dt.date_id
WHERE 
    dp.brand = 'ColaMax' 
    AND dt.year = 2024 
    AND dt.week_number = 10;
```
- **Execution Result:**
```text
 revenue
25923.57
```

## Query 13: What is the total market share of DoughBoy in the Snacks category?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Agentic SQL Engine
- **Generated SQL:** 
```sql
SELECT 
    SUM(CASE WHEN f.product_id = (SELECT product_id FROM dim_product WHERE brand = 'DoughBoy') THEN f.total_sales ELSE 0 END) / 
    SUM(f.total_sales) AS total_market_share
FROM 
    fact_internal_sales f
JOIN 
    dim_category c ON f.category_id = c.category_id
JOIN 
    dim_product p ON f.product_id = p.product_id
WHERE 
    c.category = 'Snacks'
```
- **Execution Result:**
```text
None
```

## Query 14: What was the total revenue for FizzPop in 2023?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0            NaN
```

## Query 15: What was the total revenue for ColaMax in 2023?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0            NaN
```

## Query 16: What was the total revenue for DoughBoy in 2023?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0            NaN
```

## Query 17: What was the total revenue for Zap in 2023?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0            NaN
```

## Query 18: Show me the overall total revenue for all internal brands combined.
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0    23451342.61
```

## Query 19: Which internal brand had the lowest total revenue overall?
- **Intent Predicted:** `simple_kpi`
- **Route Taken:** Deterministic KPI Engine
- **Final Response:** 
```
   total_revenue
0    23451342.61
```

## Query 20: Tell me a recipe for a chocolate cake.
- **Intent Predicted:** `unknown`
- **Route Taken:** Fallback
- **Final Response:** I'm sorry, I can only answer questions related to FMCG retail analytics.

