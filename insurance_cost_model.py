import pandas as pd

def get_insurance_costs(
    insurance_type: str,
    health_status: str,
    family_status: str,
    user_age: int = None,
    partner_age: int = None,
    years_to_simulate: int = 60
) -> tuple:
    """
    Returns annual premiums and out-of-pocket (OOP) costs over time based on insurance type, health, and family status.

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
        annual_oop = lifetime_oop_map.get(health_status, 75000) / years_to_simulate
        return [0] * years_to_simulate, [annual_oop] * years_to_simulate

    # Define cost mappings for ESI and ACA separately
    cost_structure = {
        "Employer": {
            "premium": {
                "healthy": {"single": 1541, "family": 3082},
                "chronic": {"single": 1920, "family": 3840},
                "high_risk": {"single": 2400, "family": 4800},
            },
            "oop": {
                "healthy": {"single": 2200, "family": 4400},
                "chronic": {"single": 2600, "family": 5200},
                "high_risk": {"single": 3100, "family": 6200},
            }
        },
        "Marketplace": {
            "premium": {
                "healthy": {"single": 5100, "family": 10200},
                "chronic": {"single": 5800, "family": 11600},
                "high_risk": {"single": 6800, "family": 13600},
            },
            "oop": {
                "healthy": {"single": 4500, "family": 9000},
                "chronic": {"single": 5200, "family": 10400},
                "high_risk": {"single": 6500, "family": 13000},
            }
        }
    }

    # Fallback to Employer if not specified
    insurance_key = "Employer" if insurance_type.lower() == "employer" else "Marketplace"

    premium_lookup = cost_structure[insurance_key]["premium"]
    oop_lookup = cost_structure[insurance_key]["oop"]

    if health_status == "chronic":
        chronic_years = years_to_simulate  # chronic persists for life
        premium = [premium_lookup["chronic"][family_status]] * chronic_years
        oop = [oop_lookup["chronic"][family_status]] * chronic_years
    elif health_status == "high_risk":
        high_risk_years = min(10, years_to_simulate)
        remaining_years = years_to_simulate - high_risk_years
        premium = [premium_lookup["high_risk"][family_status]] * high_risk_years
        premium += [premium_lookup["chronic"][family_status]] * remaining_years
        oop = [oop_lookup["high_risk"][family_status]] * high_risk_years
        oop += [oop_lookup["chronic"][family_status]] * remaining_years
    else:  # healthy
        premium = [premium_lookup["healthy"][family_status]] * years_to_simulate
        oop = [oop_lookup["healthy"][family_status]] * years_to_simulate

    return premium, oop
