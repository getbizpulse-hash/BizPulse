import pandas as pd
from datetime import datetime

# Service price mapping (placeholder prices)
SERVICE_PRICES = {
    "waterless pedicure": 90,
    "smart pedicure": 95,
    "e-file manicure": 55,
    "gel polish": 25,
    "nail polish": 15,
    "feet massage": 20,
    "hands massage": 15,
    "hard gel strengthening": 35,
    "nail repair": 20,
    "french tip": 15,
    "paramedical pedicure": 120,
    "consultation": 50,
    "b/s brace": 80,
    "default": 85  # fallback price
}


def estimate_price(service_str: str) -> float:
    """Estimate price from service string."""
    if pd.isna(service_str):
        return SERVICE_PRICES["default"]

    service_lower = service_str.lower()
    total = 0
    matched = False

    for service, price in SERVICE_PRICES.items():
        if service != "default" and service in service_lower:
            total += price
            matched = True

    return total if matched else SERVICE_PRICES["default"]


def validate_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate CSV has required columns."""
    required = ["client_name", "start", "status"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        return False, f"Missing required columns: {', '.join(missing)}"

    return True, "Valid"


def load_and_process_csv(uploaded_file) -> pd.DataFrame:
    """Load CSV and process into customer-level data."""
    # Read CSV
    df = pd.read_csv(uploaded_file)

    # Validate
    is_valid, message = validate_csv(df)
    if not is_valid:
        raise ValueError(message)

    # Filter to accepted appointments only
    df = df[df["status"] == "accepted"].copy()

    # Parse dates
    df["start"] = pd.to_datetime(df["start"], format="%m-%d-%Y %I:%M:%S %p", errors="coerce")

    # Estimate prices if not present
    if "estimated_total_price" not in df.columns or df["estimated_total_price"].isna().all():
        df["estimated_price"] = df["service"].apply(estimate_price)
    else:
        df["estimated_price"] = pd.to_numeric(df["estimated_total_price"], errors="coerce")
        df["estimated_price"] = df["estimated_price"].fillna(df["service"].apply(estimate_price))

    # Extract email and phone if present
    if "email" not in df.columns:
        df["email"] = None
    if "phone" not in df.columns:
        df["phone"] = None

    return df


def aggregate_to_customers(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """Aggregate transaction data to customer level."""
    # Filter by date range if provided
    if start_date:
        df = df[df["start"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["start"] <= pd.to_datetime(end_date)]

    # Aggregate by customer
    customer_df = df.groupby("client_name").agg(
        frequency=("start", "count"),
        recency=("start", "max"),
        first_visit=("start", "min"),
        total_spend=("estimated_price", "sum"),
        avg_spend=("estimated_price", "mean"),
        email=("email", "first"),
        phone=("phone", "first"),
    ).reset_index()

    # Calculate days since last visit
    today = pd.Timestamp.now()
    customer_df["days_since_visit"] = (today - customer_df["recency"]).dt.days

    return customer_df
