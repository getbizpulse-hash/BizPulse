import pandas as pd

SEGMENT_DEFINITIONS = {
    "Explorer": {"min": 1, "max": 2, "color": "#FF6B6B", "description": "1-2 visits"},
    "Casual": {"min": 3, "max": 8, "color": "#4ECDC4", "description": "3-8 visits"},
    "Regular": {"min": 9, "max": 12, "color": "#45B7D1", "description": "9-12 visits"},
    "Superuser": {"min": 13, "max": 999, "color": "#96CEB4", "description": "13+ visits"},
}


def assign_segment(frequency: int) -> str:
    """Assign segment based on visit frequency."""
    for segment, rules in SEGMENT_DEFINITIONS.items():
        if rules["min"] <= frequency <= rules["max"]:
            return segment
    return "Explorer"  # fallback


def assign_segments(customer_df: pd.DataFrame) -> pd.DataFrame:
    """Add segment column to customer DataFrame."""
    df = customer_df.copy()
    df["segment"] = df["frequency"].apply(assign_segment)
    return df


def get_segment_summary(customer_df: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics by segment."""
    summary = customer_df.groupby("segment").agg(
        customer_count=("client_name", "count"),
        total_revenue=("total_spend", "sum"),
        avg_revenue=("total_spend", "mean"),
        avg_frequency=("frequency", "mean"),
    ).reset_index()

    # Add segment order for sorting
    segment_order = {"Explorer": 0, "Casual": 1, "Regular": 2, "Superuser": 3}
    summary["order"] = summary["segment"].map(segment_order)
    summary = summary.sort_values("order").drop(columns=["order"])

    return summary
