# Business Lens AI — Architecture & Design Document

> **Version:** 1.0  
> **Author:** Utkarsh Sinha  
> **Date:** April 2026  

---

## Table of Contents

1. [Data Modeling & Assumptions](#1-data-modeling--assumptions)
2. [Metric Logic (KPIs)](#2-metric-logic-kpis)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack Rationale](#4-tech-stack-rationale)

---

## 1. Data Modeling & Assumptions

### 1.1 Raw Data Sources

The system ingests two primary CSV files with fundamentally different structures:

| Source File | Granularity | Key Columns |
|---|---|---|
| `weekly_internal_sales.csv` | **SKU × Retailer × Week** | Reported_SKU, Reported_Brand, Reported_Category, Reported_Retailer, Reported_Variant, Volume, Unit_Price, Total_Sales, Week_Start |
| `weekly_competitor_market.csv` | **Category × Retailer × Week** | Reported_Category, Reported_Retailer, Competitor_Volume, Competitor_Sales, Week_Start |

### 1.2 Entity Resolution & Data Cleaning

A core challenge is that the raw data contains extensive typos, abbreviations, and inconsistent naming across every dimension. Our pipeline applies a **4-tier resolution strategy** (implemented in `data_pipeline.py`):

| Resolution Tier | Method | Example |
|---|---|---|
| **Tier 1: Exact Match** | Lowercase lookup against a curated mapping dictionary | `"colamax"` → `ColaMax` |
| **Tier 2: Substring Match** | Checks if any known key is a substring of the input | `"megamart supercenters"` → `MegaMart` |
| **Tier 3: Fuzzy Match (Canonical)** | `difflib.get_close_matches()` against canonical values | `"ColeMex"` → `ColaMax` (cutoff ≥ 0.5) |
| **Tier 4: Fuzzy Match (Keys)** | Fuzzy match against all mapping keys | Catches extreme typos |

**Mapping dictionaries** are exhaustively defined in `keywords.py` (~1,600 lines) covering all observed variations for:

- **Brands** (8 canonical): `ColaMax`, `FizzPop`, `Zap`, `DoughBoy`, `CrunchBite`, `PotatoKing`, `SweetTreat`, `Titan`
- **Categories** (2 canonical): `Beverages`, `Snacks`
- **Retailers** (8 canonical): `MegaMart`, `FreshGrocer`, `DailyShop`, `QuickStop`, `GiantStore`, `CornerStore`, `PrimePantry`, `WebCart`
- **Variants** (~25+ canonical): `Classic`, `Diet`, `Zero Sugar`, `Cherry`, `BBQ`, `Flamin Hot`, `Honey BBQ`, `Original Salted`, `Double Choco`, `Oatmeal Raisin`, etc.

**Assumptions applied during cleaning:**

| Assumption | Rationale |
|---|---|
| **Unresolvable entities are tagged `"Unknown"`** | Prevents silent data loss; enables audit via downstream filters |
| **Missing `Total_Sales` is imputed as `Volume × Unit_Price`** | Maintains row completeness; the `is_imputed` flag preserves lineage |
| **SKU cleaning replaces `A` → `-` and `Z` → `0`** | Observed systematic corruption pattern (e.g., `SKU A1234` → `SKU-1234`) |
| **Fuzzy match cutoff is 0.5 (brands/retailers) and 0.4 (variants)** | Variants have shorter strings and more diverse abbreviations; lower threshold needed |
| **`Week_Start` is parsed as-is (no timezone adjustment)** | Data assumed to be in a single consistent timezone |

### 1.3 Final Schema — Star Schema in DuckDB

After cleaning, data is loaded into a **Star Schema** inside DuckDB:

```
                    ┌────────────────┐
                    │   dim_time     │
                    │────────────────│
                    │ date_id (PK)   │
                    │ week_start     │
                    │ year           │
                    │ month          │
                    │ quarter        │
                    │ week_number    │
                    └──────┬─────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  │                      │
┌───────┴────────┐  ┌──────┴───────────┐  ┌───────┴──────────┐
│ dim_product    │  │ fact_internal_   │  │ fact_competitor_  │
│────────────────│  │ sales            │  │ market           │
│ product_id(PK) │  │─────────────────│  │─────────────────│
│ sku_id         │  │ date_id (FK)    │  │ date_id (FK)    │
│ brand          │  │ product_id (FK) │  │ category_id (FK)│
│ variant        │  │ category_id(FK) │  │ retailer_id(FK) │
│                │  │ retailer_id(FK) │  │ competitor_vol  │
│                │  │ volume          │  │ competitor_sales│
│                │  │ total_sales     │  └─────────────────┘
│                │  │ is_imputed      │
└────────────────┘  └─────────────────┘
        
┌────────────────┐  ┌────────────────┐
│ dim_category   │  │ dim_retailer   │
│────────────────│  │────────────────│
│ category_id(PK)│  │ retailer_id(PK)│
│ category       │  │ retailer       │
└────────────────┘  └────────────────┘
```

### 1.4 Handling Mismatched Granularities

The internal sales data is at **SKU-level** while competitor data is at **Category-level**. This is resolved by:

1. **Separate fact tables**: `fact_internal_sales` (granular) and `fact_competitor_market` (aggregated) are never force-joined at conflicting grain.
2. **Shared conformed dimensions**: Both facts share `dim_time`, `dim_category`, and `dim_retailer` — enabling comparisons at the **Category × Retailer × Week** level.
3. **Market Share is computed at category grain**: When calculating market share, internal sales are first aggregated up to category level, then compared against competitor totals.

### 1.5 Hierarchy Inference

Since no explicit product hierarchy was provided, we infer:

```
Category (Beverages / Snacks)
  └── Brand (ColaMax, FizzPop, Zap, ...)
       └── Variant (Classic, Diet, Cherry, ...)
            └── SKU (SKU-XXXX)
```

This hierarchy is encoded in `dim_product` and `dim_category` via the FK relationships in the fact table.

---

## 2. Metric Logic (KPIs)

All KPIs are implemented as deterministic SQL queries in the **Semantic Metric Layer** (`kpi_engine.py`). This ensures 100% reproducibility and zero hallucination risk for standard business metrics.

### 2.1 KPI Definitions

| # | KPI Name | Formula | SQL Implementation | Sliceable By |
|---|---|---|---|---|
| 1 | **Total Revenue** | `SUM(total_sales)` | Aggregates `fact_internal_sales.total_sales` with optional year/brand filter | Year, Brand |
| 2 | **Year-over-Year (YoY) Growth** | `((Current Year Revenue - Previous Year Revenue) / Previous Year Revenue) × 100` | CTE-based: computes revenue for `year` and `year-1`, then calculates percentage delta | Year, Brand |
| 3 | **Market Share** | `Internal Sales / (Internal Sales + Competitor Sales) × 100` | Cross-joins aggregated internal and competitor sales at category level | Year, Category |

### 2.2 KPI SQL Examples

**Total Revenue (Filtered):**
```sql
SELECT ROUND(SUM(f.total_sales), 2) AS total_revenue
FROM fact_internal_sales f
JOIN dim_time t ON f.date_id = t.date_id
JOIN dim_product p ON f.product_id = p.product_id
WHERE t.year = 2024 AND p.brand = 'ColaMax'
```

**Year-over-Year Growth:**
```sql
WITH yearly_sales AS (
    SELECT t.year, SUM(f.total_sales) AS revenue
    FROM fact_internal_sales f
    JOIN dim_time t ON f.date_id = t.date_id
    WHERE t.year IN (2025, 2024)
    GROUP BY t.year
)
SELECT 
    curr.year AS current_year,
    ROUND(((curr.revenue - prev.revenue) / NULLIF(prev.revenue, 0)) * 100, 2) AS yoy_growth_percent
FROM yearly_sales curr
LEFT JOIN yearly_sales prev ON prev.year = 2024
WHERE curr.year = 2025
```

**Market Share:**
```sql
WITH internal AS (
    SELECT SUM(f.total_sales) AS internal_sales
    FROM fact_internal_sales f
    JOIN dim_time t ON f.date_id = t.date_id
    JOIN dim_category c ON f.category_id = c.category_id
    WHERE t.year = 2025 AND c.category = 'Beverages'
),
competitor AS (
    SELECT SUM(f.competitor_sales) AS competitor_sales
    FROM fact_competitor_market f
    JOIN dim_time t ON f.date_id = t.date_id
    JOIN dim_category c ON f.category_id = c.category_id
    WHERE t.year = 2025 AND c.category = 'Beverages'
)
SELECT ROUND((i.internal_sales / NULLIF(i.internal_sales + c.competitor_sales, 0)) * 100, 2) 
       AS market_share_percent
FROM internal i CROSS JOIN competitor c
```

### 2.3 Design Principles

- **Deterministic over Generative**: KPIs use hardcoded, auditable SQL — never LLM-generated queries — to guarantee correctness.
- **`NULLIF` guards**: All division operations use `NULLIF(x, 0)` to prevent division-by-zero errors.
- **`is_imputed` lineage**: The imputation flag is carried through to the fact table, allowing analysts to filter or audit imputed values.
- **`read_only` connections**: The KPI engine opens DuckDB in `read_only=True` mode to prevent accidental data mutation.

---

## 3. System Architecture

### 3.1 End-to-End Query Workflow

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────────┐     ┌──────────────┐
│   Streamlit  │────▶│  Orchestrator│────▶│   LLM Router           │────▶│  Intent      │
│   Chat UI    │     │  (Gateway)   │     │   (DeepSeek v3.1)      │     │  Category    │
│   (app.py)   │     │              │     │   via LangChain Ollama │     │              │
└──────────────┘     └──────┬───────┘     └────────────────────────┘     └──────┬───────┘
                            │                                                   │
                            │  Routes based on intent                           │
                            ▼                                                   │
              ┌─────────────────────────────────┐                               │
              │                                 │                               │
    ┌─────────┴─────────┐           ┌───────────┴───────────┐                   │
    │  DETERMINISTIC    │           │  AGENTIC PATH         │                   │
    │  KPI Engine       │           │  SQL Agent            │                   │
    │  (kpi_engine.py)  │           │  (sql_agent.py)       │                   │
    │                   │           │                       │                   │
    │ • Pre-built SQL   │           │ • LLM generates SQL   │                   │
    │ • 0% hallucination│           │ • Schema-grounded     │                   │
    │ • Fast execution  │           │ • Flexible analysis   │                   │
    └─────────┬─────────┘           └───────────┬───────────┘                   │
              │                                 │                               │
              └───────────────┬─────────────────┘                               │
                              ▼                                                 │
                    ┌──────────────────┐                                         │
                    │    DuckDB        │                                         │
                    │  Star Schema     │◀────────────────────────────────────────┘
                    │  (business_lens  │        (Schema definition used 
                    │   .duckdb)       │         in SQL Agent prompt)
                    └──────────────────┘
```

### 3.2 Routing Logic — Deterministic vs. Agentic

The **Orchestrator** (`orchestrator.py`) implements a two-stage routing decision:

```
User Query
    │
    ▼
┌──────────────────────────────────┐
│  Stage 1: LLM Intent Classifier │
│  (LLMRouter.classify())         │
│                                  │
│  Outputs one of:                 │
│   • "simple_kpi"                 │
│   • "comparison"                 │
│   • "trend_analysis"             │
│   • "unknown"                    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 2: Deterministic Guard    │
│                                  │
│  IF intent == "unknown"          │
│    → Return refusal message      │
│                                  │
│  IF intent == "simple_kpi"       │
│    AND query contains known KPI  │
│    keyword (e.g., "total revenue")│
│    → Route to KPI Engine         │
│    → Extract params (year, brand)│
│    → Execute pre-built SQL       │
│                                  │
│  ELSE (comparison, trend,        │
│        complex simple_kpi)       │
│    → Route to SQL Agent          │
│    → LLM generates SQL           │
│    → Execute against DuckDB      │
└──────────────────────────────────┘
```

#### When is the Deterministic Pipeline Used?

| Condition | Route | Rationale |
|---|---|---|
| Intent = `simple_kpi` **AND** query matches a known KPI keyword (e.g., "total revenue") | **KPI Engine** (Deterministic) | Zero hallucination risk. Pre-validated SQL. Sub-millisecond execution. |
| Intent = `comparison`, `trend_analysis`, or unmatched `simple_kpi` | **SQL Agent** (Agentic) | Queries are too varied/complex for pre-built templates. LLM generates flexible SQL grounded by schema context. |
| Intent = `unknown` | **Refusal** | Out-of-domain queries are blocked to prevent hallucination. |

#### Anti-Hallucination Safeguards

1. **Schema Grounding**: The SQL Agent prompt includes the full schema definition (table names, column types, relationships) — the LLM can only reference existing tables/columns.
2. **Read-Only Execution**: DuckDB connections use `read_only=True` — no `INSERT`, `UPDATE`, `DELETE`, or `DROP` can execute.
3. **SQL Extraction**: The agent parses only the SQL code block from the LLM response (via regex `\```sql...\````), discarding any surrounding hallucinated text.
4. **Deterministic-first routing**: Simple KPIs bypass the LLM entirely, using auditable, pre-built queries.

### 3.3 Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| **Config** | `src/config.py` | Centralized paths, environment variables, LLM settings |
| **Data Pipeline** | `src/data_pipeline.py` | Entity resolution, cleaning, imputation, time derivation |
| **Keywords** | `src/keywords.py` | Exhaustive typo→canonical mapping dictionaries |
| **DB Manager** | `src/db_manager.py` | Star schema creation, dimension/fact loading, validation |
| **KPI Engine** | `src/kpi_engine.py` | Deterministic metric layer (Total Revenue, YoY, Market Share) |
| **LLM Router** | `src/llm_router.py` | Intent classification via LLM prompt |
| **SQL Agent** | `src/sql_agent.py` | Text-to-SQL generation and execution for complex queries |
| **Orchestrator** | `src/orchestrator.py` | End-to-end query processing — ties router, KPI, and agent |
| **App** | `app.py` | Streamlit chat UI with session state and cached backend |

---

## 4. Tech Stack Rationale

### 4.1 Core Technologies

| Technology | Version | Purpose | Why This Choice? |
|---|---|---|---|
| **Python** | 3.10+ | Primary language | Industry standard for data/AI workloads; rich ecosystem |
| **DuckDB** | 1.5.2 | Analytical database | Embedded (zero-infra), columnar storage, blazing-fast OLAP queries, native Pandas integration. Ideal for analytical workloads without deploying Postgres/Snowflake. |
| **Pandas** | 3.0.2 | Data cleaning & transformation | De-facto standard for tabular data manipulation; seamless DuckDB interop via `.df()` |
| **Streamlit** | 1.57.0 | Frontend / Chat UI | Rapid prototyping of data apps with built-in chat components (`st.chat_input`, `st.chat_message`), DataFrame rendering, and caching (`@st.cache_resource`) |

### 4.2 LLM & Orchestration

| Technology | Version | Purpose | Why This Choice? |
|---|---|---|---|
| **LangChain** | 1.2.15 | LLM orchestration framework | Provides `PromptTemplate`, `StrOutputParser`, and composable chains (`prompt \| llm \| parser`). Standardizes LLM interaction patterns. |
| **LangChain-Ollama** | 1.1.0 | LLM provider integration | Connects to DeepSeek v3.1 (671B) via the Ollama-compatible API. Enables local/cloud model swapping with minimal code change. |
| **LangChain-Groq** | 1.1.2 | Alternative LLM provider | Available as a fallback for faster inference via Groq's LPU hardware. |
| **LangChain-Google-GenAI** | 4.2.2 | Alternative LLM provider | Enables switching to Gemini models if needed for production. |
| **DeepSeek v3.1 (671B)** | Cloud | Primary LLM | Strong reasoning and SQL generation capabilities at the 671B parameter scale. Used for both intent classification and Text-to-SQL. |

### 4.3 Data Cleaning & Utilities

| Technology | Purpose | Why This Choice? |
|---|---|---|
| **difflib** (stdlib) | Fuzzy string matching | Zero-dependency fuzzy matching via `get_close_matches()`. Sufficient for typo resolution without requiring `fuzzywuzzy` or `rapidfuzz`. |
| **openpyxl** | Excel I/O | Required by Pandas for `.xlsx` read/write of cleaned data exports. |
| **python-dotenv** | Environment config | Loads `.env` secrets (API keys) without hardcoding. Industry-standard secret management for local development. |

### 4.4 Architecture Decision Records (ADRs)

| Decision | Alternatives Considered | Rationale for Choice |
|---|---|---|
| **DuckDB over SQLite/Postgres** | SQLite lacks OLAP optimizations; Postgres requires server deployment | DuckDB is embedded, columnar, and optimized for analytical queries — perfect fit for a single-user analytics assistant |
| **Star Schema over Flat Tables** | Flat denormalized table | Star schema enables clean dimension reuse across two fact tables, supports drill-down queries, and is the industry standard for analytical data modeling |
| **Deterministic KPI Engine over Full LLM** | Let the LLM generate all SQL | Pre-built SQL for common KPIs eliminates hallucination risk and provides sub-ms latency. The LLM is reserved for queries that genuinely require flexibility. |
| **Hybrid Router (LLM + Rule-based)** | Pure keyword router; Pure LLM router | Keyword-only misses nuance; LLM-only is slow and can misroute. The hybrid approach uses the LLM for intent classification but applies deterministic guards for final routing. |
| **LangChain over raw API calls** | Direct `requests.post()` to LLM API | LangChain provides prompt management, output parsing, and provider abstraction. Switching between DeepSeek/Groq/Gemini requires changing only the provider class. |
| **Streamlit over Flask/FastAPI** | Flask + React frontend | Streamlit provides built-in chat UI, DataFrame rendering, and session state — dramatically reducing frontend development time for a data-focused application. |

---

*End of Architecture & Design Document*
