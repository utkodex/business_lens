import pandas as pd
import re
import difflib
from config import INTERNAL_SALES_FILE, COMPETITOR_MARKET_FILE, DATA_DIR

# --- 1. ENTITY RESOLUTION MAPPINGS ---

from keywords import BRAND_MAP, CATEGORY_MAP, RETAILER_MAP, VARIANT_MAP

# Pre-compute lowercase maps and canonical sets for robust fuzzy matching
V_MAP_LOWER = {str(k).lower(): v for k, v in VARIANT_MAP.items()}
R_MAP_LOWER = {str(k).lower(): v for k, v in RETAILER_MAP.items()}
C_MAP_LOWER = {str(k).lower(): v for k, v in CATEGORY_MAP.items()}
B_MAP_LOWER = {str(k).lower(): v for k, v in BRAND_MAP.items()}

CANONICAL_BRANDS = list(set(BRAND_MAP.values()))
CANONICAL_CATEGORIES = list(set(CATEGORY_MAP.values()))
CANONICAL_RETAILERS = list(set(RETAILER_MAP.values()))
CANONICAL_VARIANTS = list(set(VARIANT_MAP.values()))

def clean_entity(x, mapping, canonicals, cutoff=0.5):
    """
    Generalized robust cleaning function. Uses exact mapping, 
    substring matching, and fuzzy matching to resolve typos.
    """
    if pd.isna(x): return "Unknown"
    s = str(x).lower().strip()
    
    # 1. Exact match against lowercased keys
    if s in mapping: 
        return mapping[s]
        
    # 2. Substring match
    for k, v in mapping.items():
        if k in s: 
            return v
            
    # 3. Fuzzy match against canonical values
    matches = difflib.get_close_matches(str(x), canonicals, n=1, cutoff=cutoff)
    if matches: 
        return matches[0]
        
    # 4. Fuzzy match against mapped keys
    matches_lower = difflib.get_close_matches(s, mapping.keys(), n=1, cutoff=cutoff)
    if matches_lower: 
        return mapping[matches_lower[0]]
        
    return "Unknown"

# --- 2. CLEANING FUNCTIONS ---

def clean_sku(raw_sku: str) -> str:
    """
    Cleans and canonicalizes a raw SKU string by fixing common typos (e.g., A to -, Z to 0) 
    and extracting the standard SKU format (SKU-XXXX).
    """
    if pd.isna(raw_sku):
        return raw_sku
    s = str(raw_sku).upper().strip()
    s = s.replace('A', '-').replace('Z', '0')
    match = re.search(r'(\d{4})', s)
    if match:
        return f"SKU-{match.group(1)}"
    return s

def clean_retailer(raw_retailer: str) -> str:
    """
    Cleans and canonicalizes a raw retailer string. Uses robust fuzzy mapping.
    """
    return clean_entity(raw_retailer, R_MAP_LOWER, CANONICAL_RETAILERS, cutoff=0.5)

def clean_variant(raw_variant: str) -> str:
    """
    Cleans and canonicalizes a product variant. Uses robust fuzzy mapping.
    """
    return clean_entity(raw_variant, V_MAP_LOWER, CANONICAL_VARIANTS, cutoff=0.4)

def clean_internal_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the raw internal sales DataFrame. Normalizes SKUs, Brands, Categories, Retailers,
    and Variants. Imputes missing sales data and derives time dimensions. Returns a cleaned DataFrame.
    """
    df = df.copy()
    
    # 1. Normalize SKU
    df['sku_id'] = df['Reported_SKU'].apply(clean_sku)
    
    # 2. Normalize Brand
    df['brand'] = df['Reported_Brand'].apply(lambda x: clean_entity(x, B_MAP_LOWER, CANONICAL_BRANDS, cutoff=0.5))
    
    # 3. Normalize Category
    df['category'] = df['Reported_Category'].apply(lambda x: clean_entity(x, C_MAP_LOWER, CANONICAL_CATEGORIES, cutoff=0.5))
    
    # 4. Normalize Retailer
    df['retailer'] = df['Reported_Retailer'].apply(clean_retailer)
    
    # 5. Normalize Variant
    df['variant'] = df['Reported_Variant'].apply(clean_variant)
    
    # 6. Impute missing Total_Sales
    def impute_sales(row):
        """
        Nested function to impute missing Total_Sales values by multiplying Volume by Unit_Price.
        """
        try:
            return float(row['Total_Sales'])
        except (ValueError, TypeError):
            if pd.notna(row['Volume']) and pd.notna(row['Unit_Price']):
                return float(row['Volume']) * float(row['Unit_Price'])
            return None
            
    df['total_sales'] = df.apply(impute_sales, axis=1)
    df['is_imputed'] = df['Total_Sales'].isna() | (df['Total_Sales'] == '')
    
    # 7. Parse dates
    df['week_start'] = pd.to_datetime(df['Week_Start'])
    
    # 8. Derive time dimensions
    df['year'] = df['week_start'].dt.year
    df['month'] = df['week_start'].dt.month
    df['quarter'] = df['week_start'].dt.quarter
    df['week_number'] = df['week_start'].dt.isocalendar().week
    
    return df

def clean_competitor_market(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the raw competitor market DataFrame. Normalizes Categories and Retailers
    and parses week start dates. Returns a cleaned DataFrame.
    """
    df = df.copy()
    
    df['category'] = df['Reported_Category'].apply(lambda x: clean_entity(x, C_MAP_LOWER, CANONICAL_CATEGORIES, cutoff=0.5))
    df['retailer'] = df['Reported_Retailer'].apply(clean_retailer)
    df['week_start'] = pd.to_datetime(df['Week_Start'])
    
    return df

# --- 3. EXECUTION BLOCK ---

if __name__ == "__main__":
    print("--- Checkpoint 2: Data Cleaning Pipeline ---")
    
    print("Loading raw internal sales...")
    internal_df = pd.read_csv(INTERNAL_SALES_FILE)
    print(f"Raw shape: {internal_df.shape}")
    
    print("Cleaning internal sales...")
    clean_internal = clean_internal_sales(internal_df)
    print(f"Cleaned shape: {clean_internal.shape}")
    print("\nSample Cleaned Internal Data (first 3 rows):")
    cols_to_show = ['week_start', 'sku_id', 'brand', 'category', 'retailer', 'variant', 'Volume', 'total_sales', 'is_imputed']
    print(clean_internal[cols_to_show].head(3).to_string())
    
    print("\nLoading raw competitor market...")
    comp_df = pd.read_csv(COMPETITOR_MARKET_FILE)
    print(f"Raw shape: {comp_df.shape}")
    
    print("Cleaning competitor market...")
    clean_comp = clean_competitor_market(comp_df)
    print(f"Cleaned shape: {clean_comp.shape}")
    print("\nSample Cleaned Competitor Data (first 3 rows):")
    comp_cols = ['week_start', 'category', 'retailer', 'Competitor_Volume', 'Competitor_Sales']
    print(clean_comp[comp_cols].head(3).to_string())
    
    print("\nExporting cleaned data to Excel...")
    excel_path = DATA_DIR / "cleaned_data.xlsx"
    
    # Writing both dataframes to separate sheets in a single Excel file
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        clean_internal.to_excel(writer, sheet_name='internal data', index=False)
        clean_comp.to_excel(writer, sheet_name='compititor data', index=False)
        
    print(f"Data successfully exported to: {excel_path}")
    print("\n[SUCCESS] Checkpoint 2 passed: Pipeline ran successfully.")
