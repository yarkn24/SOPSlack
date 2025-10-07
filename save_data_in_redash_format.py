"""
Save Training/Test/Validation Data in Redash Format
====================================================
Uses EXACT same split logic from ultra_fast_training.py
ONLY converts format (numeric → text)
DOES NOT touch amount or split logic!

Usage:
    python save_data_in_redash_format.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from data_mapping import PAYMENT_METHOD_REVERSE, ACCOUNT_REVERSE
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("SAVING DATA IN REDASH FORMAT")
print("=" * 80)
print()

# ============================================================================
# STEP 1: LOAD AND PROCESS DATA (EXACT SAME AS ultra_fast_training.py)
# ============================================================================

print("📂 Loading original data...")
# Data location: Desktop/cursor_data (organized workspace)
data_path = '/Users/yarkin.akcil/Desktop/cursor_data/Unrecon_2025_10_05_updated.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"   Loaded from: {data_path}")
print(f"   Total rows: {len(df):,}")

# Process (EXACT same as training script)
df['amount'] = df['amount'] / 100  # ← Correct format (already divided by 100)
df['date'] = pd.to_datetime(df['date'], format='mixed')
df = df[df['date'] >= '2024-01-01'].copy()
df = df[df['agent'].notna()].copy()

# Remove SVB (EXACT same as training script)
svb_accounts = [1, 2, 5, 10, 24]
df = df[~df['origination_account_id'].isin(svb_accounts)].copy()

# Normalize agent (EXACT same)
df['agent'] = df['agent'].str.strip()

print(f"✅ After processing: {len(df):,} transactions | {df['agent'].nunique()} agents")
print()

# ============================================================================
# STEP 2: SPLIT DATA (EXACT SAME LOGIC AS ultra_fast_training.py)
# ============================================================================

print("🔪 Splitting data (temporal split)...")

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Split dates
split_date_1 = '2024-09-01'
split_date_2 = '2024-10-01'

train_data = df[df['date'] < split_date_1].copy()
test_data = df[(df['date'] >= split_date_1) & (df['date'] < split_date_2)].copy()
val_data = df[df['date'] >= split_date_2].copy()

print(f"   Train: {len(train_data):,} (before {split_date_1})")
print(f"   Test:  {len(test_data):,} ({split_date_1} to {split_date_2})")
print(f"   Val:   {len(val_data):,} (after {split_date_2})")
print()

# ============================================================================
# STEP 3: CONVERT TO REDASH FORMAT
# ============================================================================

def convert_to_redash_format(df, name):
    """
    Convert numeric codes to text (Redash format).
    DOES NOT touch amount!
    """
    print(f"🔄 Converting {name} to Redash format...")
    
    df_new = df.copy()
    
    # Convert payment_method: number → text
    df_new['payment_method'] = df_new['payment_method'].map(
        lambda x: PAYMENT_METHOD_REVERSE.get(int(x) if pd.notna(x) else -1, 'unknown')
    )
    
    # Convert origination_account_id → account: number → text
    df_new['account'] = df_new['origination_account_id'].map(
        lambda x: ACCOUNT_REVERSE.get(int(x) if pd.notna(x) else -1, 'Unknown Account')
    )
    
    # Select and reorder columns to match Redash format
    # REDASH FORMAT: id, description, amount, date, payment_method, account, agent
    columns_to_keep = ['id', 'description', 'amount', 'date', 'payment_method', 'account', 'agent']
    df_new = df_new[columns_to_keep]
    
    print(f"   ✅ Converted {len(df_new):,} rows")
    print(f"   ✅ Columns: {list(df_new.columns)}")
    print(f"   ✅ Sample amounts (unchanged): {df_new['amount'].head(3).tolist()}")
    print()
    
    return df_new

# Convert each dataset
train_redash = convert_to_redash_format(train_data, "Training Data")
test_redash = convert_to_redash_format(test_data, "Test Data")
val_redash = convert_to_redash_format(val_data, "Validation Data")

# ============================================================================
# STEP 4: SAVE TO CSV
# ============================================================================

print("💾 Saving to CSV files (Desktop/cursor_data)...")

output_dir = '/Users/yarkin.akcil/Desktop/cursor_data'

train_redash.to_csv(f'{output_dir}/train_data_redash_format.csv', index=False)
print(f"   ✅ train_data_redash_format.csv ({len(train_redash):,} rows)")

test_redash.to_csv(f'{output_dir}/test_data_redash_format.csv', index=False)
print(f"   ✅ test_data_redash_format.csv ({len(test_redash):,} rows)")

val_redash.to_csv(f'{output_dir}/val_data_redash_format.csv', index=False)
print(f"   ✅ val_data_redash_format.csv ({len(val_redash):,} rows)")

print()

# ============================================================================
# STEP 5: VERIFICATION
# ============================================================================

print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print()

print("📊 Row counts:")
print(f"   Training:   {len(train_redash):,}")
print(f"   Test:       {len(test_redash):,}")
print(f"   Validation: {len(val_redash):,}")
print(f"   TOTAL:      {len(train_redash) + len(test_redash) + len(val_redash):,}")
print()

print("📋 Column format (all datasets):")
print(f"   Columns: {list(train_redash.columns)}")
print()

print("💰 Amount verification (NOT modified):")
print(f"   Training amounts:   {train_redash['amount'].describe()['mean']:.2f} (mean)")
print(f"   Test amounts:       {test_redash['amount'].describe()['mean']:.2f} (mean)")
print(f"   Validation amounts: {val_redash['amount'].describe()['mean']:.2f} (mean)")
print()

print("📝 Sample data (Training):")
print(train_redash.head(2))
print()

print("🎉 SUCCESS! All data saved in Redash format.")
print("   ✅ Split logic preserved (temporal split)")
print("   ✅ Amount unchanged (correct format)")
print("   ✅ Format converted (numeric → text)")
