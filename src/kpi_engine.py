import pandas as pd
import duckdb
from config import DUCKDB_FILE

class KPIEngine:
    """
    Semantic Metric Layer for querying pre-defined business KPIs.
    Uses DuckDB to execute optimized SQL queries against the Star Schema.
    """
    def __init__(self, db_path=DUCKDB_FILE):
        self.db_path = str(db_path)
        
    def _execute(self, query: str) -> pd.DataFrame:
        # Use read_only=True since we are only querying data, avoiding write locks
        with duckdb.connect(self.db_path, read_only=True) as conn:
            return conn.execute(query).df()
            
    def get_total_revenue(self, year: int = None, brand: str = None) -> pd.DataFrame:
        """
        Calculates Total Revenue. Can be sliced by year and brand.
        """
        where_clauses = []
        if year:
            where_clauses.append(f"t.year = {year}")
        if brand:
            where_clauses.append(f"p.brand = '{brand}'")
            
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
        query = f'''
        SELECT 
            ROUND(SUM(f.total_sales), 2) as total_revenue
        FROM fact_internal_sales f
        JOIN dim_time t ON f.date_id = t.date_id
        JOIN dim_product p ON f.product_id = p.product_id
        {where_sql}
        '''
        return self._execute(query)

    def get_yoy_growth(self, year: int, brand: str = None) -> pd.DataFrame:
        """
        Calculates Year-over-Year (YoY) revenue growth percent.
        Compares `year` with `year - 1`.
        """
        prev_year = year - 1
        
        brand_filter = ""
        if brand:
            brand_filter = f"AND p.brand = '{brand}'"
            
        query = f'''
        WITH yearly_sales AS (
            SELECT 
                t.year,
                SUM(f.total_sales) as revenue
            FROM fact_internal_sales f
            JOIN dim_time t ON f.date_id = t.date_id
            JOIN dim_product p ON f.product_id = p.product_id
            WHERE t.year IN ({year}, {prev_year}) {brand_filter}
            GROUP BY t.year
        )
        SELECT 
            curr.year as current_year,
            ROUND(curr.revenue, 2) as current_year_revenue,
            ROUND(prev.revenue, 2) as previous_year_revenue,
            ROUND(((curr.revenue - prev.revenue) / NULLIF(prev.revenue, 0)) * 100, 2) as yoy_growth_percent
        FROM yearly_sales curr
        LEFT JOIN yearly_sales prev ON prev.year = {prev_year}
        WHERE curr.year = {year}
        '''
        return self._execute(query)
        
    def get_market_share(self, year: int = None, category: str = None) -> pd.DataFrame:
        """
        Calculates internal market share percent.
        Market Share = Internal Sales / (Internal Sales + Competitor Sales)
        """
        where_i = []
        where_c = []
        
        if year:
            where_i.append(f"t.year = {year}")
            where_c.append(f"t.year = {year}")
        if category:
            where_i.append(f"c.category = '{category}'")
            where_c.append(f"c.category = '{category}'")
            
        where_i_sql = "WHERE " + " AND ".join(where_i) if where_i else ""
        where_c_sql = "WHERE " + " AND ".join(where_c) if where_c else ""
        
        query = f'''
        WITH internal AS (
            SELECT SUM(f.total_sales) as internal_sales
            FROM fact_internal_sales f
            JOIN dim_time t ON f.date_id = t.date_id
            JOIN dim_category c ON f.category_id = c.category_id
            {where_i_sql}
        ),
        competitor AS (
            SELECT SUM(f.competitor_sales) as competitor_sales
            FROM fact_competitor_market f
            JOIN dim_time t ON f.date_id = t.date_id
            JOIN dim_category c ON f.category_id = c.category_id
            {where_c_sql}
        )
        SELECT 
            ROUND(i.internal_sales, 2) as internal_sales,
            ROUND(c.competitor_sales, 2) as competitor_sales,
            ROUND(i.internal_sales + c.competitor_sales, 2) as total_market_sales,
            ROUND((i.internal_sales / NULLIF(i.internal_sales + c.competitor_sales, 0)) * 100, 2) as market_share_percent
        FROM internal i
        CROSS JOIN competitor c
        '''
        return self._execute(query)


if __name__ == "__main__":
    print("--- Checkpoint 4: Deterministic KPI Logic ---")
    
    # Initialize the engine
    engine = KPIEngine()
    
    print("\n1. Total Revenue (Overall):")
    df_revenue = engine.get_total_revenue()
    print(df_revenue.to_string(index=False))
    
    print("\n2. Total Revenue (ColaMax, 2024):")
    df_revenue_filtered = engine.get_total_revenue(year=2024, brand="ColaMax")
    print(df_revenue_filtered.to_string(index=False))
    
    print("\n3. YoY Growth (2025 vs 2024):")
    df_yoy = engine.get_yoy_growth(year=2025)
    print(df_yoy.to_string(index=False))
    
    print("\n4. Market Share (2025, Beverages):")
    df_share = engine.get_market_share(year=2025, category="Beverages")
    print(df_share.to_string(index=False))
    
    print("\n[SUCCESS] Checkpoint 4 passed: KPI queries executed successfully.")
