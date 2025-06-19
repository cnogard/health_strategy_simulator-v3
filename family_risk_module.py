import streamlit as st

from projected_health_risk import get_risk_trajectory

def evaluate_family_risk(user_profile):
    risks = {}

    # User
    risks["user"] = get_risk_trajectory(user_profile["age"], user_profile["health_status"])

    # Partner
    if user_profile.get("family_status") == "family" and user_profile.get("partner_age") is not None:
        partner_status = user_profile.get("partner_health_status", "healthy")
        risks["partner"] = get_risk_trajectory(user_profile["partner_age"], partner_status)

    # Dependents
    dep_ages = user_profile.get("dependent_ages", [])
    dep_healths = user_profile.get("dependent_health_statuses", [])
    for i, (age, status) in enumerate(zip(dep_ages, dep_healths)):
        risks[f"dependent_{i+1}"] = get_risk_trajectory(age, status)

    # Average risk per year
    trajectory_length = len(next(iter(risks.values())))
    avg_risk_by_year = [
        sum(r[year] for r in risks.values() if len(r) > year) / len(risks)
        for year in range(trajectory_length)
    ]

    high_risk_flags = [name for name, r in risks.items() if max(r) >= 0.9]

    return {
        "individual_trajectories": risks,
        "avg_family_risk": avg_risk_by_year,
        "high_risk_members": high_risk_flags
    }

def get_family_risk_summary(user_profile, dependents=None, partner_age=None, partner_health_status=None):
    """
    Compute a simplified risk summary for partner and dependents.
    """

    summary = {}

    if user_profile.get("family_status") == "family":
        partner_risk = 0.3  # default baseline
        partner_status = user_profile.get("partner_health_status", "healthy")
        if partner_status == "chronic":
            partner_risk = 0.6
        elif partner_status == "high_risk":
            partner_risk = 0.9
        summary["Partner"] = {
            "age": user_profile.get("partner_age"),
            "health_status": partner_status,
            "risk_score": partner_risk
        }

        dependents = user_profile.get("num_dependents", 0)
        dependent_ages = user_profile.get("dependent_ages", [])
        for i in range(dependents):
            age = dependent_ages[i] if i < len(dependent_ages) else None
            child_risk = 0.3 if age and age < 10 else 0.4
            summary[f"Child_{i+1}"] = {
                "age": age,
                "risk_score": child_risk
            }

    return summary


# New function: adjust_risk_after_capital_strategy
import math

def adjust_risk_after_capital_strategy(family_risk_dict, capital_investment_level):
    """
    Adjusts average family risk based on capital strategy. A higher investment can reduce risk modestly over time.

    Parameters:
    - family_risk_dict: dict output from evaluate_family_risk
    - capital_investment_level: float from 0 to 1 indicating capital strength (e.g., 0.25 for low, 0.75 for high)

    Returns:
    - modified copy of family_risk_dict with adjusted avg_family_risk
    """
    adjusted = family_risk_dict.copy()
    original_curve = family_risk_dict["avg_family_risk"]
    decay = min(max(capital_investment_level, 0.0), 1.0)

    adjusted_curve = []
    for i, risk in enumerate(original_curve):
        adjustment = (1 - 0.25 * capital_investment_level)  # example linear reduction, tune as needed
        adjusted_value = round(max(0, risk * adjustment), 4)
        adjusted_curve.append(adjusted_value)

    adjusted["avg_family_risk"] = adjusted_curve
    return adjusted