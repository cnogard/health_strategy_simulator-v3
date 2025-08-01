def get_oop_correction_ratio(age, insurance_type, health_status):
    insurance_type = insurance_type.lower()
    health_status = health_status.lower()

    if age < 45:
        age_key = "under_45"
    elif age <= 54:
        age_key = "45_54"
    elif age <= 64:
        age_key = "55_64"
    else:
        age_key = "65_plus"

    if insurance_type in ["medicare", "traditional medicare"]:
        insurance_key = "traditional_medicare"
    elif insurance_type in ["medicare advantage"]:
        insurance_key = "medicare_advantage"
    else:
        insurance_key = "any"

    if health_status == "healthy":
        health_key = "healthy"
    else:
        health_key = "chronic_or_high"

    table = {
        "under_45": {"any": {"healthy": 1.0, "chronic_or_high": 1.1}},
        "45_54": {"any": {"healthy": 1.2, "chronic_or_high": 1.4}},
        "55_64": {"any": {"healthy": 1.6, "chronic_or_high": 2.0}},
        "65_plus": {
            "medicare_advantage": {"healthy": 2.5, "chronic_or_high": 3.0},
            "traditional_medicare": {"healthy": 3.5, "chronic_or_high": 4.0},
        },
    }

    try:
        return table[age_key][insurance_key][health_key]
    except KeyError:
        return 1.0  # Fallback for unexpected cases


def get_base_oop(insurance_type, family_status):
    """
    Returns the base out-of-pocket cost based on insurance type and family status.
    """
    oop_lookup = {
        "ESI": {"single": 1800, "family": 3600},
        "ACA": {"single": 4800, "family": 9600},
        "Uninsured": {"single": 6500, "family": 13000}
    }
    return oop_lookup.get(insurance_type, {}).get(family_status, 0)


def get_base_premium(insurance_type, family_status):
    """
    Returns the base premium based on insurance type and family status.
    """
    premium_lookup = {
        "ESI": {"single": 1401, "family": 6575},
        "ACA": {"single": 5472, "family": 11738},
        "Uninsured": {"single": 0, "family": 0}
    }
    return premium_lookup.get(insurance_type, {}).get(family_status, 0)

def get_insurance_costs_over_time(profile, years):
    family_status = profile.get("family_status", "single")
    insurance_type = profile.get("insurance_type", "ESI")
    health_status = profile.get("health_status", "healthy")
    age = profile.get("age", 30)


    # Duration logic for chronic and high-risk
    chronic_duration = years  # Chronic conditions persist through life
    high_risk_duration = 10  # High-risk is assumed to last 10 years

    print(f"DEBUG: Base Premium: {base_premium}, Base OOP: {base_oop}")

    national_premiums = {
        "esi": {"single": 1401, "family": 6575},
        "aca": {"single": 5472, "family": 11738},
        "medicare_advantage": {"single": 1200, "family": 2400},
        "traditional_medicare": {"single": 1800, "family": 3600}
    }

    national_oop = {
        "esi": {"single": 1800, "family": 3600},
        "aca": {"single": 4800, "family": 9600},
        "medicare_advantage": {"single": 4000, "family": 8000},
        "traditional_medicare": {"single": 6000, "family": 12000}
    }

    uninsured_oop = {"single": 6500, "family": 13000}

    premium_list = []
    oop_list = []

    # Normalize insurance key for lookup
    insurance_type_key = insurance_type.lower().replace(" ", "_")

    for i in range(years):
        current_age = age + i

        # Duration-based health status logic
        if health_status == "high_risk" and i >= high_risk_duration:
            current_health_status = "chronic"
        else:
            current_health_status = health_status

        age_factor = 1 + 0.03 * max(current_age - 30, 0)
        risk_factor = get_oop_correction_ratio(current_age, insurance_type, current_health_status)

        if insurance_type_key == "uninsured":
            # Use fallback lifetime cost logic for uninsured
            if current_health_status == "healthy":
                lifetime_cost = 75000
            elif current_health_status == "chronic":
                lifetime_cost = 459000
            else:
                lifetime_cost = 472000
            years_remaining = max(1, 85 - current_age)
            avg_annual_cost = lifetime_cost / years_remaining
            premium = 0
            oop = avg_annual_cost

        elif insurance_type_key == "esi":
            base_premium = national_premiums["esi"][family_status]
            base_oop = national_oop["esi"][family_status]
            premium = base_premium * age_factor * risk_factor
            oop = base_oop * age_factor * risk_factor

        elif insurance_type_key == "aca":
            base_premium = national_premiums["aca"][family_status]
            base_oop = national_oop["aca"][family_status]
            premium = base_premium * age_factor * risk_factor
            oop = base_oop * age_factor * risk_factor

        elif insurance_type_key in ["medicare_advantage", "traditional_medicare"]:
            base_premium = national_premiums[insurance_type_key][family_status]
            base_oop = national_oop[insurance_type_key][family_status]
            premium = base_premium * age_factor * risk_factor
            oop = base_oop * age_factor * risk_factor

        else:
            # Default fallback logic
            premium = base_premium * age_factor * risk_factor
            oop = base_oop * age_factor * risk_factor

        premium_list.append(premium)
        oop_list.append(oop)

    return {"premium": premium_list, "oop": oop_list}