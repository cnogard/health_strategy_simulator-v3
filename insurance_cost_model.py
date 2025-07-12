import pandas as pd

def get_insurance_costs(insurance_type: str, health_status: str, family_status: str, years: int = 60) -> tuple:
    """
    Returns annual premium and out-of-pocket (OOP) costs over time based on insurance type, health and family status.

    Parameters:
    - insurance_type: "uninsured" or other recognized insurance types
    - health_status: "healthy", "chronic", or "high_risk"
    - family_status: "single" or "family"
    - years: Number of years to return (default 60)

    Returns:
    - Tuple of (premium_list, oop_list), each with length `years`
    """

    # === Restored validated fallback logic for uninsured users (based on PMC10314135) ===
    if insurance_type == "uninsured":
        lifetime_oop_map = {
            "healthy": 75000,
            "chronic": 459000,
            "high_risk": 472000,
        }
        annual_oop = lifetime_oop_map.get(health_status, 75000) / years
        return [0] * years, [annual_oop] * years

    premium_lookup = {
        "healthy": {"single": 1600, "family": 3200},
        "chronic": {"single": 1920, "family": 3840},
        "high_risk": {"single": 2400, "family": 4800},
    }

    oop_lookup = {
        "healthy": {"single": 1800, "family": 3600},
        "chronic": {"single": 2160, "family": 4320},
        "high_risk": {"single": 2700, "family": 5400},
    }

    if health_status == "chronic":
        chronic_years = years  # chronic persists for life
        premium = [premium_lookup["chronic"][family_status]] * chronic_years
        oop = [oop_lookup["chronic"][family_status]] * chronic_years
    elif health_status == "high_risk":
        high_risk_years = min(10, years)
        remaining_years = years - high_risk_years
        premium = [premium_lookup["high_risk"][family_status]] * high_risk_years
        premium += [premium_lookup["chronic"][family_status]] * remaining_years
        oop = [oop_lookup["high_risk"][family_status]] * high_risk_years
        oop += [oop_lookup["chronic"][family_status]] * remaining_years
    else:  # healthy
        premium = [premium_lookup["healthy"][family_status]] * years
        oop = [oop_lookup["healthy"][family_status]] * years

    return premium, oop
