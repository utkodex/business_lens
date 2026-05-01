# Business Lens AI - Executive Category Intelligence

## 📸 Application Previews
<p align="center">
  <img src="https://github.com/utkodex/business_lens/blob/main/media/1.jpeg?raw=true" width="48%" />
  <img src="https://github.com/utkodex/business_lens/blob/main/media/2.jpeg?raw=true" width="48%" />
</p>
<p align="center">
  <img src="https://github.com/utkodex/business_lens/blob/main/media/3.jpeg?raw=true" width="48%" />
  <img src="https://github.com/utkodex/business_lens/blob/main/media/4.jpeg?raw=true" width="48%" />
</p>
<p align="center">
  <img src="https://github.com/utkodex/business_lens/blob/main/media/5.jpeg?raw=true" width="48%" />
  <img src="https://github.com/utkodex/business_lens/blob/main/media/6.jpeg?raw=true" width="48%" />
</p>

## Overview
Business Lens AI is an enterprise-grade AI analytics assistant built for the Category Heads of the Beverages and Snacks divisions. This platform replaces scattered, poorly governed legacy data extracts by providing a unified, conversational interface capable of answering complex queries about market trends, YoY growth, and competitor baselines.

## ✅ Project Deliverables & Status

### Mandatory Deliverables
- [x] **Build Log with AI session links** ([ChatGPT Conversation Link](https://chatgpt.com/share/69f344ab-33fc-83e8-b32d-d9ccfd922591))
- [x] **Architecture & Design Document** ([ARCHITECTURE.md](ARCHITECTURE.md))
- [x] **Hosted Working Prototype** ([🔗 Live Demo](https://business-lens-demo.onrender.com/))
- [x] **GitHub/Workflow Assets** (Clean code, README, and logs)
- [x] **Executive Presentation Deck** ([Report Directory](report/))

### Prototype Expectations
- [x] **Multi-agent architecture** ([ARCHITECTURE.md](ARCHITECTURE.md))
- [x] **Conversational AI assistant** ([Screenshot 1](https://raw.githubusercontent.com/utkodex/business_lens/refs/heads/main/media/1.jpeg), [Screenshot 2](https://raw.githubusercontent.com/utkodex/business_lens/refs/heads/main/media/2.jpeg))
- [x] **Data modeling from messy datasets** ([DuckDB Star Schema](src/sql_agent.py#L17-L30))
- [x] **KPI generation** ([src/kpi_engine.py](src/kpi_engine.py))
- [x] **Query answering capability** ([src/orchestrator.py](src/orchestrator.py))
- [x] **Deployed accessible application** ([🔗 Live on Render](https://business-lens-demo.onrender.com/) | [Dockerfile](Dockerfile))

---

## 📊 The Data Context
The raw materials for this project consisted of two legacy datasets:
1. `weekly_internal_sales_messy.csv`
2. `weekly_competitor_market_messy.csv`
3. `Data Dictionary.xlsx`

Because there was no centralized Master Data Management (MDM) table or clean product hierarchy provided, a robust data cleaning and modeling pipeline was built. The pipeline ingests the raw data, infers product hierarchies, resolves mismatches in granularities across internal and competitor data, and loads the cleaned data into an embedded analytical database.

## 🏗️ Architecture & Design Document (Deliverable 2)

### Data Modeling & Assumptions
- **DuckDB Star Schema:** The underlying data architecture leverages DuckDB for extremely fast in-memory and embedded analytical processing.
- **Hierarchy Inference:** Entities and hierarchies were resolved by scanning and normalizing brand, category, and sub-category names to create a unified dimension table.
- **Granularity Handling:** Since competitor data and internal data arrived in different structures, they were mapped against a common time dimension (Weeks/Quarters/Years) to allow for comparative aggregations.

### Metric Logic
- Core KPIs tracked include:
  - **Total Revenue / Sales Volume:** Aggregated weekly and dynamically rollable to monthly/quarterly.
  - **YoY Growth:** Calculated dynamically via window functions or relative time filtering in SQL.
  - **Market Share:** Derived by dividing internal brand sales by total competitor + internal sales within a category.

### System Architecture
The application uses a **Multi-Agent Architecture** with a hybrid routing approach:
1. **User Request:** The user submits a query through the Streamlit interface.
2. **Deterministic LLM Router:** The query hits the `LLMRouter` which classifies the intent (e.g., `DATA_QUERY`, `CASUAL`).
3. **Agentic SQL Execution:** If it's a data query, the `SQLAgent` (powered by LangChain) dynamically interacts with the DuckDB schema. It reads table structures, generates compliant SQL, validates the query against DuckDB, executes it, and synthesizes the final conversational response.
4. **Prevention of Hallucinations:** The LLM is forced to output valid SQL against the physical schema. The final answer strictly utilizes the results of the executed SQL, making it deterministic and 100% traceable.

### Tech Stack Rationale
- **FastAPI:** Used as the decoupleable backend API to manage the agents and provide a RESTful interface. Highly scalable.
- **Streamlit:** Serves as the interactive, chat-based frontend, delivering a premium ChatGPT-like UI experience.
- **DuckDB:** Replaces slow Pandas workflows with blazing-fast analytical SQL execution locally.
- **LangChain / Groq / Ollama:** Used for multi-agent orchestration. The app supports dynamic provider switching between Groq (Cloud/Fast via LLaMA 3.3) and Ollama (Local/Cloud via DeepSeek-v3).
- **Docker:** Used for containerization and production deployment.

## 🚀 Prototype Artifacts (Deliverable 3)
- **Hosted Demo URL:** [https://business-lens-demo.onrender.com/](https://business-lens-demo.onrender.com/)
- **Source Code / Repo:** [https://github.com/utkodex/business_lens](https://github.com/utkodex/business_lens)
- **Query Execution Logs Report:** A comprehensive log of 20 test queries run through the Multi-Agent pipeline (including Intent Classification, Generated SQL, and final execution DataFrames) can be found in the repository here: [`report/query_logs_report.md`](report/query_logs_report.md).

## 🛠️ Build Log & AI Usage (Deliverable 1)
This project utilized iterative building and AI-assisted workflows to accelerate development, debugging, and styling.
- **AI Chat Link(s):** [ChatGPT Conversation Link](https://chatgpt.com/share/69f344ab-33fc-83e8-b32d-d9ccfd922591) (Project assistance and development logs)

## 📈 Executive Readout & Roadmap (Deliverable 4)
- **Accuracy & Traceability:** By generating SQL instead of text, users can trace the exact query the AI ran against the database. SQL syntax is validated before execution.
- **Performance:** Using Groq provides near-instantaneous token generation (Llama 3.3). Future bottlenecks could include extremely large database scans in DuckDB, which would require pre-aggregated materialized views.
- **Production Roadmap:** 
  - Implementation of Row-Level Security (RLS) to restrict category access based on the user's role.
  - Migration from an embedded DuckDB file to a managed Cloud Data Warehouse (e.g., Snowflake, BigQuery) for scale.
  - Addition of a "Download Data" feature for the generated tables.
