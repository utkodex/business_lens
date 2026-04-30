import os
import duckdb
import pandas as pd
from config import DUCKDB_FILE, INTERNAL_SALES_FILE, COMPETITOR_MARKET_FILE
from data_pipeline import clean_internal_sales, clean_competitor_market

def setup_database(db_path=DUCKDB_FILE):
    """
    Ensure the db directory exists and return a DuckDB connection.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))

def create_schema_and_load_data(conn, df_internal, df_competitor):
    """
    Creates Star Schema tables (dimensions and facts) and populates them using the cleaned DataFrames.
    """
    print("Preparing dimensions...")
    
    # 1. Dim Time
    time_i = df_internal[['week_start', 'year', 'month', 'quarter', 'week_number']].drop_duplicates()
    
    # Ensure df_competitor has time components for a complete time dimension
    if 'year' not in df_competitor.columns:
        df_competitor['year'] = df_competitor['week_start'].dt.year
        df_competitor['month'] = df_competitor['week_start'].dt.month
        df_competitor['quarter'] = df_competitor['week_start'].dt.quarter
        df_competitor['week_number'] = df_competitor['week_start'].dt.isocalendar().week
    
    time_c = df_competitor[['week_start', 'year', 'month', 'quarter', 'week_number']].drop_duplicates()
    
    dim_time = pd.concat([time_i, time_c]).drop_duplicates().sort_values('week_start').reset_index(drop=True)
    dim_time['date_id'] = dim_time.index + 1
    
    # 2. Dim Product (SKU, Brand, Variant) - only in internal sales
    dim_product = df_internal[['sku_id', 'brand', 'variant']].drop_duplicates().reset_index(drop=True)
    dim_product['product_id'] = dim_product.index + 1
    
    # 3. Dim Category
    cat_i = df_internal[['category']].drop_duplicates()
    cat_c = df_competitor[['category']].drop_duplicates()
    dim_category = pd.concat([cat_i, cat_c]).drop_duplicates().reset_index(drop=True)
    dim_category['category_id'] = dim_category.index + 1
    
    # 4. Dim Retailer
    ret_i = df_internal[['retailer']].drop_duplicates()
    ret_c = df_competitor[['retailer']].drop_duplicates()
    dim_retailer = pd.concat([ret_i, ret_c]).drop_duplicates().reset_index(drop=True)
    dim_retailer['retailer_id'] = dim_retailer.index + 1
    
    print("Registering dataframes to DuckDB...")
    # Register dataframes to DuckDB so we can query them with SQL
    conn.register('dim_time_df', dim_time)
    conn.register('dim_product_df', dim_product)
    conn.register('dim_category_df', dim_category)
    conn.register('dim_retailer_df', dim_retailer)
    conn.register('df_internal', df_internal)
    conn.register('df_competitor', df_competitor)
    
    print("Creating tables...")
    # Create Dimension Tables
    conn.execute("CREATE TABLE IF NOT EXISTS dim_time AS SELECT * FROM dim_time_df")
    conn.execute("CREATE TABLE IF NOT EXISTS dim_product AS SELECT * FROM dim_product_df")
    conn.execute("CREATE TABLE IF NOT EXISTS dim_category AS SELECT * FROM dim_category_df")
    conn.execute("CREATE TABLE IF NOT EXISTS dim_retailer AS SELECT * FROM dim_retailer_df")
    
    # Create Fact Tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fact_internal_sales AS
        SELECT 
            t.date_id,
            p.product_id,
            c.category_id,
            r.retailer_id,
            i.Volume as volume,
            i.total_sales,
            i.is_imputed
        FROM df_internal i
        JOIN dim_time_df t ON i.week_start = t.week_start
        JOIN dim_product_df p ON i.sku_id = p.sku_id AND i.brand = p.brand AND i.variant = p.variant
        JOIN dim_category_df c ON i.category = c.category
        JOIN dim_retailer_df r ON i.retailer = r.retailer
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fact_competitor_market AS
        SELECT 
            t.date_id,
            c.category_id,
            r.retailer_id,
            cm.Competitor_Volume as competitor_volume,
            cm.Competitor_Sales as competitor_sales
        FROM df_competitor cm
        JOIN dim_time_df t ON cm.week_start = t.week_start
        JOIN dim_category_df c ON cm.category = c.category
        JOIN dim_retailer_df r ON cm.retailer = r.retailer
    ''')
    
    print("Star schema built successfully.")

def run_validations(conn):
    """
    Runs basic validation queries against the newly created database tables.
    """
    print("\n--- Validating Database Schema ---")
    
    tables = ['dim_time', 'dim_product', 'dim_category', 'dim_retailer', 'fact_internal_sales', 'fact_competitor_market']
    print("Table Row Counts:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  - {table}: {count}")
        
    null_sales = conn.execute("SELECT COUNT(*) FROM fact_internal_sales WHERE total_sales IS NULL").fetchone()[0]
    print(f"\nNull 'total_sales' in fact_internal_sales: {null_sales}")
    
    print("\nSample Join (Internal Sales with Dimensions):")
    query = '''
    SELECT 
        t.week_start, 
        p.brand, 
        c.category, 
        r.retailer, 
        f.volume,
        f.total_sales
    FROM fact_internal_sales f
    JOIN dim_time t ON f.date_id = t.date_id
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_category c ON f.category_id = c.category_id
    JOIN dim_retailer r ON f.retailer_id = r.retailer_id
    LIMIT 5
    '''
    df_join = conn.execute(query).df()
    print(df_join.to_string(index=False))

if __name__ == "__main__":
    print("--- Checkpoint 3: Database & Schema ---")
    
    # Start fresh for development runs
    if DUCKDB_FILE.exists():
        print(f"Removing existing database at {DUCKDB_FILE} to start fresh...")
        os.remove(DUCKDB_FILE)
        
    print("Loading and cleaning internal sales data...")
    df_internal = clean_internal_sales(pd.read_csv(INTERNAL_SALES_FILE))
    
    print("Loading and cleaning competitor market data...")
    df_comp = clean_competitor_market(pd.read_csv(COMPETITOR_MARKET_FILE))
    
    print("\nConnecting to DuckDB...")
    db_conn = setup_database()
    
    create_schema_and_load_data(db_conn, df_internal, df_comp)
    
    run_validations(db_conn)
    db_conn.close()
    
    print("\n[SUCCESS] Checkpoint 3 passed: Database populated successfully.")
