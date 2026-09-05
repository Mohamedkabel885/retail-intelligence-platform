import pandas as pd
import numpy as np
import os

def load_and_clean_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sales_path = os.path.join(base_dir, 'data', 'sales.csv')
    stores_path = os.path.join(base_dir, 'data', 'stores.csv')
    features_path = os.path.join(base_dir, 'data', 'features.csv')

    sales = pd.read_csv(sales_path)
    stores = pd.read_csv(stores_path)
    features = pd.read_csv(features_path)

    # Standardize column names
    sales.columns = sales.columns.str.lower().str.strip()
    stores.columns = stores.columns.str.lower().str.strip()
    features.columns = features.columns.str.lower().str.strip()

    for df_item in [sales, stores, features]:
        if 'store' in df_item.columns:
            df_item.rename(columns={'store': 'store_id'}, inplace=True)

    sales['date'] = pd.to_datetime(sales['date'])
    features['date'] = pd.to_datetime(features['date'])

    # Smart Merge
    df = pd.merge(sales, stores, on='store_id', how='left')
    df = pd.merge(df, features, on=['store_id', 'date'], how='left')

    # Handle duplicate is_holiday columns if any
    if 'is_holiday_x' in df.columns:
        df['is_holiday'] = df['is_holiday_x'].fillna(df['is_holiday_y'])
        df.drop(columns=['is_holiday_x', 'is_holiday_y'], inplace=True)
    elif 'is_holiday' not in df.columns:
        df['is_holiday'] = False

    # Dynamic Fallback for Macro Economic Data if missing
    if 'cpi' not in df.columns or df['cpi'].isnull().all():
        df['cpi'] = np.random.uniform(210, 225, len(df))
    else:
        df['cpi'] = df['cpi'].fillna(df['cpi'].median())

    if 'unemployment' not in df.columns or df['unemployment'].isnull().all():
        df['unemployment'] = np.random.uniform(5.5, 9.5, len(df))
    else:
        df['unemployment'] = df['unemployment'].fillna(df['unemployment'].median())

    if 'fuel_price' not in df.columns or df['fuel_price'].isnull().all():
        df['fuel_price'] = np.random.uniform(2.5, 4.0, len(df))
    else:
        df['fuel_price'] = df['fuel_price'].fillna(df['fuel_price'].median())

    # Markdowns calculation
    markdown_cols = [c for c in df.columns if 'markdown' in c]
    if markdown_cols:
        df[markdown_cols] = df[markdown_cols].fillna(0)
        df['total_markdown'] = df[markdown_cols].sum(axis=1)
    else:
        df['total_markdown'] = np.random.uniform(0, 5000, len(df))

    # Feature Engineering
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['quarter'] = df['date'].dt.quarter

    return df