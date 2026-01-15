import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln
from typing import Tuple, Dict


def zt_nbd_log_likelihood(params: Tuple[float, float], frequency_counts: pd.Series) -> float:
    """
    Zero-Truncated Negative Binomial log-likelihood.

    params: (r, alpha) - shape and rate parameters
    frequency_counts: Series with index = visit count, values = number of customers
    """
    r, alpha = params

    if r <= 0 or alpha <= 0:
        return 1e10

    ll = 0
    p_zero = (alpha / (alpha + 1)) ** r  # P(X=0) for standard NBD

    for x, count in frequency_counts.items():
        if x < 1 or count == 0:
            continue

        # NBD probability
        log_p_x = (
            gammaln(r + x) - gammaln(r) - gammaln(x + 1)
            + r * np.log(alpha / (alpha + 1))
            + x * np.log(1 / (alpha + 1))
        )

        # Zero-truncated adjustment
        log_p_x_zt = log_p_x - np.log(1 - p_zero)

        ll += count * log_p_x_zt

    return -ll  # Return negative for minimization


def fit_zt_nbd(customer_df: pd.DataFrame) -> Dict:
    """
    Fit Zero-Truncated NBD model to customer frequency data.

    Returns dict with r, alpha, f0 (estimated unobserved), and fit statistics.
    """
    # Get frequency distribution
    freq_counts = customer_df["frequency"].value_counts().sort_index()
    n_observed = len(customer_df)

    # Initial parameter guesses
    mean_freq = customer_df["frequency"].mean()
    var_freq = customer_df["frequency"].var()

    # Method of moments starting values
    if var_freq > mean_freq:
        r_init = mean_freq ** 2 / (var_freq - mean_freq)
        alpha_init = mean_freq / (var_freq - mean_freq)
    else:
        r_init = 1.0
        alpha_init = 1.0

    # Optimize
    result = minimize(
        zt_nbd_log_likelihood,
        x0=[max(0.1, r_init), max(0.1, alpha_init)],
        args=(freq_counts,),
        method="L-BFGS-B",
        bounds=[(0.01, 100), (0.01, 100)]
    )

    r, alpha = result.x

    # Calculate P(X=0) to estimate unobserved customers
    p_zero = (alpha / (alpha + 1)) ** r

    # f0 = N_observed * P(0) / (1 - P(0))
    f0 = n_observed * p_zero / (1 - p_zero)

    # Total market size
    total_market = n_observed + f0
    market_reached = n_observed / total_market

    # Model fit - chi-square (simplified)
    predicted_counts = []
    for x in freq_counts.index:
        log_p_x = (
            gammaln(r + x) - gammaln(r) - gammaln(x + 1)
            + r * np.log(alpha / (alpha + 1))
            + x * np.log(1 / (alpha + 1))
        )
        p_x_zt = np.exp(log_p_x) / (1 - p_zero)
        predicted_counts.append(p_x_zt * n_observed)

    predicted_series = pd.Series(predicted_counts, index=freq_counts.index)

    # Chi-square statistic
    chi_sq = ((freq_counts - predicted_series) ** 2 / predicted_series).sum()
    df = len(freq_counts) - 2  # degrees of freedom

    # Interpret heterogeneity
    if r < 0.5:
        heterogeneity = "high"
        hetero_desc = "Your customers are very different from each other"
    elif r < 1.5:
        heterogeneity = "moderate"
        hetero_desc = "Your customers have moderately varied visit patterns"
    else:
        heterogeneity = "low"
        hetero_desc = "Your customers have fairly similar visit patterns"

    # Model fit quality
    if chi_sq / max(df, 1) < 2:
        fit_quality = "good"
        fit_desc = "This model fits your data well"
    elif chi_sq / max(df, 1) < 4:
        fit_quality = "moderate"
        fit_desc = "This model captures most patterns, treat estimates as directional"
    else:
        fit_quality = "poor"
        fit_desc = "This model has limited fit, estimates are rough approximations"

    return {
        "r": r,
        "alpha": alpha,
        "f0": f0,
        "n_observed": n_observed,
        "total_market": total_market,
        "market_reached": market_reached,
        "chi_square": chi_sq,
        "df": df,
        "log_likelihood": -result.fun,
        "heterogeneity": heterogeneity,
        "hetero_desc": hetero_desc,
        "fit_quality": fit_quality,
        "fit_desc": fit_desc,
        "freq_actual": freq_counts,
        "freq_predicted": predicted_series,
        "avg_visits": customer_df["frequency"].mean(),
    }


def fit_gamma_gamma(customer_df: pd.DataFrame) -> Dict:
    """
    Fit Gamma-Gamma model for CLV prediction.

    Simplified implementation - estimates expected monetary value.
    """
    # Filter to customers with 2+ transactions (required for Gamma-Gamma)
    repeat_customers = customer_df[customer_df["frequency"] >= 2].copy()

    if len(repeat_customers) < 10:
        return {
            "success": False,
            "message": "Need at least 10 repeat customers for CLV analysis"
        }

    # Simple CLV estimation based on frequency and monetary value
    repeat_customers["clv"] = repeat_customers["avg_spend"] * repeat_customers["frequency"] * 1.2  # 1.2 = growth factor

    # Summary stats
    avg_clv = repeat_customers["clv"].mean()
    total_clv = repeat_customers["clv"].sum()
    top_10_pct = repeat_customers.nlargest(int(len(repeat_customers) * 0.1) or 1, "clv")["clv"].mean()

    # Find "hidden gems" - high avg spend but low frequency
    all_customers = customer_df.copy()
    all_customers["projected_clv_if_regular"] = all_customers["avg_spend"] * 12  # If they visited monthly

    hidden_gems = all_customers[
        (all_customers["frequency"] <= 4) &
        (all_customers["avg_spend"] > all_customers["avg_spend"].median())
    ].nlargest(10, "avg_spend")

    return {
        "success": True,
        "repeat_customers": repeat_customers,
        "avg_clv": avg_clv,
        "total_clv": total_clv,
        "top_10_pct_clv": top_10_pct,
        "hidden_gems": hidden_gems,
        "n_repeat": len(repeat_customers)
    }


def calculate_churn_probability(customer_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate churn probability based on recency and frequency.

    Simplified BG/NBD-inspired calculation.
    """
    df = customer_df.copy()

    # Normalize recency and frequency
    max_days = df["days_since_visit"].max()
    max_freq = df["frequency"].max()

    # Churn probability increases with days since visit, decreases with frequency
    df["recency_score"] = df["days_since_visit"] / max_days if max_days > 0 else 0
    df["frequency_score"] = 1 - (df["frequency"] / max_freq) if max_freq > 0 else 0

    # Combined churn probability (weighted)
    df["p_churn"] = (df["recency_score"] * 0.7 + df["frequency_score"] * 0.3)
    df["p_churn"] = df["p_churn"].clip(0, 1)

    # Classify risk level
    def risk_level(p):
        if p >= 0.7:
            return "high"
        elif p >= 0.4:
            return "medium"
        else:
            return "low"

    df["risk_level"] = df["p_churn"].apply(risk_level)

    return df


def get_churn_summary(customer_df: pd.DataFrame) -> Dict:
    """Get summary statistics for churn analysis."""
    df = calculate_churn_probability(customer_df)

    high_risk = df[df["risk_level"] == "high"]
    medium_risk = df[df["risk_level"] == "medium"]
    low_risk = df[df["risk_level"] == "low"]

    # Revenue at risk (from high-risk customers)
    revenue_at_risk = high_risk["total_spend"].sum() * 0.8  # Assume 80% at risk

    # Still active (low churn probability)
    still_active_pct = len(low_risk) / len(df) if len(df) > 0 else 0

    return {
        "customer_df": df,
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "low_risk_count": len(low_risk),
        "revenue_at_risk": revenue_at_risk,
        "still_active_pct": still_active_pct,
        "high_risk_customers": high_risk,
    }
