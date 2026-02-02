import pandas as pd
import re
from datetime import datetime
import numpy as np

# =============================================================================
# PROFILES & DEFINITIONS
# =============================================================================

REQUIRED_FIELDS = {
    "date": "Transaction Date",
    "amount": "Total Amount",
    "customer_id": "Customer Identifier",
    "status": "Status"
}

OPTIONAL_FIELDS = {
    "transaction_id": "Transaction ID",
    "item": "Service / Item",
    "location": "Location"
}

# Known profiles to preload mappings
PROFILES = {
    "Square": {
        "mappings": {
            "date": ["Date", "Transaction Date"],
            "amount": ["Total Collected", "Net Sales"],
            "customer_id": ["Customer Name", "Customer ID"],
            "status": ["Status"]
        }
    },
    "Toast": {
        "mappings": {
            "date": ["Opened"],
            "amount": ["Net Amount"],
            "customer_id": ["Guest Name"],
            "status": ["Void Status"]
        }
    },
    "Shopify": {
        "mappings": {
            "date": ["Created at"],
            "amount": ["Total"],
            "customer_id": ["Email"],
            "status": ["Financial Status"]
        }
    },
    "Appointments (Generic)": {
         "mappings": {
            "date": ["start", "Appointment Date", "Start Time"],
            "amount": ["price", "cost", "estimated_total_price", "Amount"],
            "customer_id": ["client_name", "Customer", "Client"],
            "status": ["status", "State"]
        }
    }
}

# =============================================================================
# HEURISTICS
# =============================================================================

def detect_source(df):
    """
    Simple heuristic to detect the source based on column presence.
    """
    cols = set(df.columns)
    
    if {"Device Name", "Card Entry Methods"}.intersection(cols):
        return "Square"
    if {"Void Status", "Discount Amount"}.intersection(cols):
        return "Toast"
    if {"Financial Status", "Fulfillment Status"}.intersection(cols):
        return "Shopify"
    if {"client_name", "estimated_total_price"}.intersection(cols):
        return "Appointments (Generic)"
        
    return "Generic CSV"

def get_column_suggestions(df, source="Generic CSV"):
    """
    Returns a dict of suggestions for each required field.
    {
        "date": {"col": "start", "confidence": "High"},
        ...
    }
    """
    columns = list(df.columns)
    suggestions = {}
    
    # helper regex lists
    regex_map = {
        "date": [r'date', r'time', r'start', r'created', r'opened'],
        "amount": [r'total', r'amount', r'price', r'cost', r'sales', r'value'],
        "customer_id": [r'customer', r'client', r'email', r'phone', r'guest', r'name'],
        "status": [r'status', r'state', r'type']
    }

    # 1. Check Profile first
    profile_map = PROFILES.get(source, {}).get("mappings", {})
    
    for field in REQUIRED_FIELDS:
        found = False
        confidence = "Low"
        
        # Check profile exact matches
        if field in profile_map:
            for candidate in profile_map[field]:
                if candidate in columns:
                    suggestions[field] = {"col": candidate, "confidence": "High"}
                    found = True
                    break
        
        # Fallback to Regex Heuristics
        if not found:
            # Look for regex match
            patterns = regex_map.get(field, [])
            for pattern in patterns:
                matches = [c for c in columns if re.search(pattern, c, re.IGNORECASE)]
                if matches:
                    # Pick shortest match usually (e.g. "Date" vs "Date of Birth")
                    best_match = min(matches, key=len)
                    suggestions[field] = {"col": best_match, "confidence": "Medium"}
                    found = True
                    break
        
        if not found:
            suggestions[field] = {"col": None, "confidence": "None"}

    return suggestions

# =============================================================================
# VALIDATION & CLEANING
# =============================================================================

def validate_mappings(df, mappings):
    """
    Basic validation to ensure required fields are mapped.
    """
    missing = []
    for field, label in REQUIRED_FIELDS.items():
        col = mappings.get(field)
        if not col or col not in df.columns:
            missing.append(label)
            
    return missing

def clean_currency(val):
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        # Remove currency symbols and commons
        clean = re.sub(r'[$,()\s]', '', val)
        try:
            return float(clean)
        except:
            return 0.0
    return 0.0

def clean_date(val):
    try:
        return pd.to_datetime(val)
    except:
        return pd.NaT

def generate_validation_summary(df, mappings, rules):
    """
    Returns statistics about the data based on mappings and rules.
    Does NOT modify the dataframe in place, but returns a summary dict.
    """
    
    date_col = mappings.get('date')
    status_col = mappings.get('status')
    cust_col = mappings.get('customer_id')
    
    # 1. Filter by Status
    included_statuses = [s.lower() for s in rules.get('included_statuses', [])]
    
    # Normalize status column for checking
    # Note: efficient pandas operation
    if status_col:
        # We simulate the filter
        status_series = df[status_col].astype(str).str.lower()
        # Simple keywords logic if "completed" is selected
        # If the user selects "completed", we look for "complete", "paid", "accepted"
        # This logic might need to be more robust or user-configurable actually
        # For now, let's assume the rules passed in ARE the actual values to match or broad categories
        
        # Quick fallback logic just for the summary:
        # If rules says "completed", we match "complete", "done", "paid", "accepted"
        pass
    
    # For MVP, we will do a 'dry run' of cleaning to get stats
    clean_df = df.copy()
    
    # Rename columns temporarily
    rename_map = {v: k for k, v in mappings.items() if v}
    clean_df = clean_df.rename(columns=rename_map)
    
    summary = {
        "total_rows": len(df),
        "clean_rows": 0,
        "excluded_rows": 0,
        "unique_customers": 0,
        "date_range": "N/A",
        "warnings": []
    }
    
    # Status Filtering
    if 'status' in clean_df.columns:
        # Normalize
        clean_df['status_norm'] = clean_df['status'].astype(str).str.lower()
        
        # Default logic: if user wants 'completed', we include reasonable positive statuses
        # If rules has specific text values, use those. 
        # For now, let's assume we filter out 'cancelled', 'refunded', 'void' if default rules apply
        
        negative_statuses = ['cancelled', 'canceled', 'refunded', 'void', 'failed', 'declined']
        mask = ~clean_df['status_norm'].apply(lambda x: any(ns in x for ns in negative_statuses))
        
        summary['excluded_rows'] = len(clean_df) - mask.sum()
        clean_df = clean_df[mask]
    
    # Date Parsing (to check range)
    if 'date' in clean_df.columns:
        clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce')
        valid_dates = clean_df.dropna(subset=['date'])
        if not valid_dates.empty:
            start = valid_dates['date'].min().strftime('%b %Y')
            end = valid_dates['date'].max().strftime('%b %Y')
            summary['date_range'] = f"{start} – {end}"
        else:
            summary['warnings'].append("Could not parse dates in the selected column.")
            
    # Customer Count
    if 'customer_id' in clean_df.columns:
        summary['unique_customers'] = clean_df['customer_id'].nunique()
        missing_cust = clean_df['customer_id'].isna().sum()
        if missing_cust > 0:
            summary['warnings'].append(f"{missing_cust} rows missing customer identifier.")
            
    summary['clean_rows'] = len(clean_df)
    
    return summary

def process_and_finalize(df, mappings, rules):
    """
    The final function to return the usable dataframe for the app.
    Renames columns to standard expected by the app: start, estimated_price, client_name.
    Filters and types correctly.
    """
    # 1. Rename to Internal Standard (Legacy Compatibility)
    # Map Wizard keys (date, amount, customer_id) -> App keys (start, estimated_price, client_name)
    target_map = {
        'date': 'start',
        'amount': 'estimated_price',
        'customer_id': 'client_name',
        'status': 'status'
    }
    
    # Invert readings: {UserCol: WizardKey}
    # We want {UserCol: AppKey}
    final_rename = {}
    for key, user_col in mappings.items():
        if user_col and key in target_map:
            final_rename[user_col] = target_map[key]
            
    final_df = df.rename(columns=final_rename)
    
    # 2. Status Filter
    if 'status' in final_df.columns:
         # Normalize
        final_df['status_norm'] = final_df['status'].astype(str).str.lower()
        negative_statuses = ['cancelled', 'canceled', 'refunded', 'void', 'failed', 'declined']
        # Filter
        final_df = final_df[~final_df['status_norm'].apply(lambda x: any(ns in x for ns in negative_statuses))]
        # Drop temp
        final_df = final_df.drop(columns=['status_norm'])
        
    # 3. Clean Types
    if 'start' in final_df.columns:
        final_df['start'] = pd.to_datetime(final_df['start'], errors='coerce')
        
    if 'estimated_price' in final_df.columns:
        final_df['estimated_price'] = final_df['estimated_price'].apply(clean_currency)
    
    # 4. Drop N/A dates (crucial for time series)
    if 'start' in final_df.columns:
        final_df = final_df.dropna(subset=['start'])
    
    return final_df
