#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEM-CAN Dataset Preprocessing Utilities
========================================

This script provides example preprocessing functions for the GEM-CAN dataset.
Users can adapt these utilities to their specific research needs.

Dataset files:
- GEM_Normal_Driving_Raw_labeled.csv (labeled baseline, all label=0)
- GEM_Attack_Scenario_Raw_Labeled.csv (labeled attacks, label=0/1, Attack_Type field)

QUICK START:
-----------
# Example 1: Basic cleaning
>>> df = pd.read_csv('GEM_Attack_Scenario_Raw_Labeled.csv')
>>> df_clean = clean_can_data(df)

# Example 2: Add features
>>> df_features = add_temporal_features(df_clean)

# Example 3: Create train/test split
>>> train_df, test_df = create_train_test_split(df_clean, test_size=0.3)
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# SECTION 1: DATA LOADING AND BASIC CLEANING
# =============================================================================

def load_gem_can_data(filepath: str, verbose: bool = True) -> pd.DataFrame:
    """
    Load GEM-CAN raw dataset from CSV file.
    
    Parameters
    ----------
    filepath : str
        Path to the CSV file
    verbose : bool
        Print loading information (default: True)
    
    Returns
    -------
    pd.DataFrame
        Loaded dataset
    
    Example
    -------
    >>> df = load_gem_can_data('GEM_Normal_Driving_Raw.csv')
    >>> print(df.shape)
    (100000, 12)
    """
    df = pd.read_csv(filepath)
    
    if verbose:
        print(f"Loaded: {filepath}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        if 'label' in df.columns:
            print(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df


def clean_can_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize CAN bus data.
    
    Operations:
    - Strip whitespace from column names
    - Standardize timestamp column name
    - Clean data bytes (replace missing values with '00')
    - Uppercase hexadecimal values
    - Remove '0x' prefix from CAN IDs
    
    Parameters
    ----------
    df : pd.DataFrame
        Raw CAN data
    
    Returns
    -------
    pd.DataFrame
        Cleaned dataset
    
    Example
    -------
    >>> df_raw = pd.read_csv('GEM_Attack_Scenario_Raw.csv')
    >>> df_clean = clean_can_data(df_raw)
    >>> print('timestamp' in df_clean.columns)
    True
    """
    df = df.copy()
    
    df.columns = df.columns.str.strip()
    
    if 'tiTestaTp' in df.columns and 'timestamp' not in df.columns:
        df.rename(columns={'tiTestaTp': 'timestamp'}, inplace=True)
        print("Renamed 'tiTestaTp' → 'timestamp'")
    
    for i in range(8):
        col = f'data{i}'
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.upper()
                .replace(['', 'NAN', 'NONE'], '00')
            )
    
    if 'arbitration_id' in df.columns:
        df['arbitration_id'] = df['arbitration_id'].astype(str).str.replace('0x', '', case=False)
    
    return df


# =============================================================================
# SECTION 2: LABEL PROCESSING
# =============================================================================

def standardize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize label column and create Attack_Type field.
    
    Converts binary labels to descriptive categories:
    - 'R' or 0 → 'Normal'
    - 'T' or 1 → 'Attack'
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'label' column
    
    Returns
    -------
    pd.DataFrame
        Dataset with Attack_Type column
    
    Example
    -------
    >>> df = pd.DataFrame({'label': [0, 1, 0]})
    >>> df_labeled = standardize_labels(df)
    >>> print(df_labeled['Attack_Type'].tolist())
    ['Normal', 'Attack', 'Normal']
    """
    df = df.copy()
    
    if 'label' not in df.columns:
        warnings.warn("No 'label' column found.")
        return df
    
    df['label'] = df['label'].astype(str).str.strip().str.upper()
    
    # Support both R/T (legacy) and 0/1 (current) label encodings
    df['Attack_Type'] = df['label'].map({
        'R': 'Normal', '0': 'Normal',
        'T': 'Attack', '1': 'Attack'
    })
    df['Attack_Type'].fillna('Unknown', inplace=True)
    
    return df


def identify_attack_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify specific attack types based on CAN ID patterns.
    
    Attack type classification:
    - CAN ID 0 or 00000000 → DoS
    - CAN ID 0x18FF00F9 → Brake Tampering
    - CAN ID 0x18FF70F9 → Steering Tampering
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'label' and 'arbitration_id' columns
    
    Returns
    -------
    pd.DataFrame
        Dataset with refined Attack_Type
    
    Example
    -------
    >>> df = clean_can_data(pd.read_csv('GEM_Attack_Scenario_Raw_Labeled.csv'))
    >>> df = standardize_labels(df)
    >>> df = identify_attack_types(df)
    >>> print(df['Attack_Type'].value_counts())
    """
    df = df.copy()
    
    if 'Attack_Type' not in df.columns:
        df = standardize_labels(df)
    
    # Support both 'T'/'1' and 'Attack' labels
    attack_mask = (df['label'] == 'T') | (df['label'] == '1') | (df['Attack_Type'] == 'Attack')
    
    dos_mask = attack_mask & ((df['arbitration_id'].str.upper() == '0') | 
                              (df['arbitration_id'].str.upper() == '00000000'))
    df.loc[dos_mask, 'Attack_Type'] = 'DoS'
    
    brake_mask = attack_mask & (df['arbitration_id'].str.upper() == '18FF00F9')
    df.loc[brake_mask, 'Attack_Type'] = 'Brake Tampering'
    
    steer_mask = attack_mask & (df['arbitration_id'].str.upper() == '18FF70F9')
    df.loc[steer_mask, 'Attack_Type'] = 'Steering Tampering'
    
    return df


# =============================================================================
# SECTION 3: FEATURE ENGINEERING
# =============================================================================

def calculate_inter_arrival_time(df: pd.DataFrame, group_by_id: bool = True) -> pd.Series:
    """
    Calculate Inter-Arrival Time (IAT) for CAN messages.
    
    IAT measures the time difference between consecutive messages,
    either globally or per CAN ID.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'timestamp' column
    group_by_id : bool
        Calculate IAT per arbitration_id (default: True)
    
    Returns
    -------
    pd.Series
        Inter-arrival times in seconds
    
    Example
    -------
    >>> df['iat'] = calculate_inter_arrival_time(df)
    >>> print(df['iat'].describe())
    """
    if 'timestamp' not in df.columns:
        raise ValueError("Dataset must contain 'timestamp' column")
    
    if group_by_id and 'arbitration_id' in df.columns:
        df_sorted = df.sort_values(['arbitration_id', 'timestamp'])
        iat = df_sorted.groupby('arbitration_id')['timestamp'].diff()
    else:
        df_sorted = df.sort_values('timestamp')
        iat = df_sorted['timestamp'].diff()
    
    return iat.fillna(0)


def calculate_message_frequency(df: pd.DataFrame, window_size: int = 50) -> pd.Series:
    """
    Calculate frequency of each CAN ID in a sliding window.
    
    For each message, counts how many times its CAN ID appears
    in the previous N messages.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'arbitration_id' column
    window_size : int
        Number of previous messages to consider (default: 50)
    
    Returns
    -------
    pd.Series
        Frequency counts (0 to window_size)
    
    Example
    -------
    >>> df['id_count_prev50'] = calculate_message_frequency(df, 50)
    >>> print(df[['arbitration_id', 'id_count_prev50']].head())
    """
    if 'arbitration_id' not in df.columns:
        raise ValueError("Dataset must contain 'arbitration_id' column")
    
    if 'timestamp' in df.columns:
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
    else:
        df_sorted = df.reset_index(drop=True)
    
    frequencies = []
    
    for i in range(len(df_sorted)):
        window_start = max(0, i - window_size)
        window_df = df_sorted.iloc[window_start:i]
        
        if len(window_df) == 0:
            count = 0
        else:
            current_id = df_sorted.iloc[i]['arbitration_id']
            count = (window_df['arbitration_id'] == current_id).sum()
        
        frequencies.append(count)
    
    return pd.Series(frequencies, index=df_sorted.index)


def add_temporal_features(df: pd.DataFrame, window_size: int = 50) -> pd.DataFrame:
    """
    Add temporal and statistical features to the dataset.
    
    Features added:
    - iat: Inter-arrival time
    - id_count_prev{N}: Message frequency in sliding window
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataset
    window_size : int
        Window size for frequency calculation (default: 50)
    
    Returns
    -------
    pd.DataFrame
        Dataset with added features
    
    Example
    -------
    >>> df_features = add_temporal_features(df, window_size=50)
    >>> print(df_features.columns.tolist())
    """
    df = df.copy()
    
    print("Calculating inter-arrival time (IAT)...")
    df['iat'] = calculate_inter_arrival_time(df)
    
    print(f"Calculating ID frequency (window={window_size})...")
    df[f'id_count_prev{window_size}'] = calculate_message_frequency(df, window_size)
    
    return df


# =============================================================================
# SECTION 4: DATASET OPERATIONS
# =============================================================================

def extract_normal_traffic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only normal traffic records.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'label' column
    
    Returns
    -------
    pd.DataFrame
        Subset containing only normal traffic (label='R' or label=0)
    """
    if 'label' not in df.columns:
        raise ValueError("Dataset must contain 'label' column")
    
    # Handle both R/T and 0/1 encodings
    normal_df = df[(df['label'] == 'R') | (df['label'] == 0) | (df['label'] == '0')].copy()
    print(f"Extracted {len(normal_df)} normal frames")
    return normal_df


def extract_attack_traffic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only attack traffic records.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset with 'label' column
    
    Returns
    -------
    pd.DataFrame
        Subset containing only attack traffic (label='T' or label=1)
    """
    if 'label' not in df.columns:
        raise ValueError("Dataset must contain 'label' column")
    
    # Handle both R/T and 0/1 encodings
    attack_df = df[(df['label'] == 'T') | (df['label'] == 1) | (df['label'] == '1')].copy()
    print(f"Extracted {len(attack_df)} attack frames")
    return attack_df


def combine_datasets(dfs: List[pd.DataFrame], shuffle: bool = True, random_seed: int = 42) -> pd.DataFrame:
    """
    Combine multiple datasets into a single DataFrame.
    
    Parameters
    ----------
    dfs : List[pd.DataFrame]
        List of DataFrames to combine
    shuffle : bool
        Randomly shuffle the combined dataset (default: True)
    random_seed : int
        Random seed for reproducibility (default: 42)
    
    Returns
    -------
    pd.DataFrame
        Combined dataset
    """
    combined = pd.concat(dfs, ignore_index=True)
    
    if shuffle:
        combined = combined.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    
    print(f"Combined {len(combined)} records")
    return combined


def create_train_test_split(df: pd.DataFrame, test_size: float = 0.3, 
                            stratify_by: Optional[str] = None,
                            random_seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into training and testing sets.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataset
    test_size : float
        Proportion for testing set (default: 0.3)
    stratify_by : str, optional
        Column name for stratified splitting (e.g., 'label')
    random_seed : int
        Random seed for reproducibility (default: 42)
    
    Returns
    -------
    tuple
        (train_df, test_df)
    
    Example
    -------
    >>> train, test = create_train_test_split(df, test_size=0.3, stratify_by='label')
    """
    from sklearn.model_selection import train_test_split
    
    stratify_values = df[stratify_by] if stratify_by and stratify_by in df.columns else None
    
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_seed,
        stratify=stratify_values, shuffle=True
    )
    
    print(f"Split: {len(train_df)} train, {len(test_df)} test")
    
    if stratify_by and stratify_by in df.columns:
        print(f"\nTrain {stratify_by}:\n{train_df[stratify_by].value_counts()}")
        print(f"\nTest {stratify_by}:\n{test_df[stratify_by].value_counts()}")
    
    return train_df, test_df


# =============================================================================
# COMPLETE EXAMPLE PIPELINES
# =============================================================================

def example_1_basic_cleaning(input_file: str, output_file: str):
    """
    Example 1: Basic data cleaning
    
    Steps:
    1. Load raw data
    2. Clean and standardize
    3. Standardize labels
    4. Save cleaned data
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Data Cleaning")
    print("="*70)
    
    df = load_gem_can_data(input_file)
    df = clean_can_data(df)
    df = standardize_labels(df)
    
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved: {output_file}")
    
    return df


def example_2_feature_engineering(input_file: str, output_file: str):
    """
    Example 2: Feature engineering
    
    Steps:
    1. Load and clean data
    2. Add temporal features
    3. Save enhanced dataset
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Feature Engineering")
    print("="*70)
    
    df = load_gem_can_data(input_file, verbose=False)
    df = clean_can_data(df)
    df = standardize_labels(df)
    df = add_temporal_features(df, window_size=50)
    
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved: {output_file}")
    
    return df


def example_3_create_train_eval_sets(normal_file: str, attack_file: str):
    """
    Example 3: Create training and evaluation sets
    
    Creates:
    - GEM_Training_Normal.csv (pure normal traffic for baseline)
    - GEM_Evaluation_Mixed.csv (mixed traffic for testing)
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Training/Evaluation Sets")
    print("="*70)
    
    print("\n[1/4] Processing normal driving data...")
    df_normal = load_gem_can_data(normal_file, verbose=False)
    df_normal = clean_can_data(df_normal)
    df_normal = standardize_labels(df_normal)
    
    print("\n[2/4] Processing attack scenario data...")
    df_attack = load_gem_can_data(attack_file, verbose=False)
    df_attack = clean_can_data(df_attack)
    df_attack = standardize_labels(df_attack)
    df_attack = identify_attack_types(df_attack)
    
    print("\n[3/4] Extracting traffic types...")
    df_normal_from_attack = extract_normal_traffic(df_attack)
    df_attacks_only = extract_attack_traffic(df_attack)
    
    print("\n[4/4] Creating datasets...")
    train_df = combine_datasets([df_normal, df_normal_from_attack], shuffle=True)
    train_df.to_csv('GEM_Training_Normal.csv', index=False)
    print(f"✓ Training set: {len(train_df)} records (100% normal)")
    
    eval_normal_sample = df_normal.sample(frac=0.15, random_state=42)
    eval_df = combine_datasets([eval_normal_sample, df_attacks_only, df_normal_from_attack], shuffle=True)
    eval_df.to_csv('GEM_Evaluation_Mixed.csv', index=False)
    print(f"✓ Evaluation set: {len(eval_df)} records (mixed)")
    print(f"\n  Attack distribution:\n{eval_df['Attack_Type'].value_counts()}")
    
    return train_df, eval_df


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Main demonstration of preprocessing workflows.
    Adapt file paths and parameters to your needs.
    """
    print("\n" + "="*70)
    print("GEM-CAN DATASET PREPROCESSING UTILITIES")
    print("="*70)
    print("\nThis script demonstrates example preprocessing workflows.")
    print("Modify file paths to match your data location.\n")
    
    NORMAL_RAW = "GEM_Normal_Driving_Raw_labeled.csv"
    ATTACK_RAW = "GEM_Attack_Scenario_Raw_Labeled.csv"
    
    import os
    if not os.path.exists(NORMAL_RAW):
        print(f"⚠  File not found: {NORMAL_RAW}")
        print("Please update file paths in the script.")
        return
    
    if not os.path.exists(ATTACK_RAW):
        print(f"⚠  File not found: {ATTACK_RAW}")
        print("Please update file paths in the script.")
        return
    
    print("\nChoose an example to run:")
    print("  1. Basic data cleaning")
    print("  2. Feature engineering")
    print("  3. Create training/evaluation sets")
    print("  4. Run all examples")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        example_1_basic_cleaning(NORMAL_RAW, "GEM_Normal_Cleaned.csv")
    elif choice == '2':
        example_2_feature_engineering(NORMAL_RAW, "GEM_Normal_Features.csv")
    elif choice == '3':
        example_3_create_train_eval_sets(NORMAL_RAW, ATTACK_RAW)
    elif choice == '4':
        example_1_basic_cleaning(NORMAL_RAW, "GEM_Normal_Cleaned.csv")
        example_2_feature_engineering(NORMAL_RAW, "GEM_Normal_Features.csv")
        example_3_create_train_eval_sets(NORMAL_RAW, ATTACK_RAW)
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\n" + "="*70)
    print("✓ PREPROCESSING COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()