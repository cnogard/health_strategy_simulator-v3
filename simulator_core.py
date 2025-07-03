import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


def generate_costs(profile, care_preferences):
    ages = list(range(profile["age"], 86))
    base_cost = 2000
    cost_data = []

    for i, age in enumerate(ages):
        insurance_type = profile.get("insurance_type", "None")
        # Chronic illness adjustment
        if profile.get("health_status") == "chronic":
            base_cost = 6500
            chronic_inflation = st.session_state.get("expense_inflation", 0.05) + 0.02
            years_since_start = age - profile["age"]
            total_cost = base_cost * ((1 + chronic_inflation) ** years_since_start)

            oop = total_cost * (
                0.15 if insurance_type == "Employer"
                else 0.2 if insurance_type == "Marketplace"
                else 0.5
            )

            base_premium = 1500 if insurance_type == "Employer" else 1800 if insurance_type == "Marketplace" else 0
            premium = base_premium * ((1 + chronic_inflation) ** years_since_start)

            print(f"--- Chronic Cost Debug ---")
            print(f"Age: {age}")
            print(f"Years Since Start: {years_since_start}")
            print(f"Base Cost: {base_cost}")
            print(f"Chronic Inflation Rate: {chronic_inflation:.4f}")
            print(f"Total Healthcare Cost: {total_cost:.2f}")
            print(f"OOP Cost: {oop:.2f}")
            print(f"Premium: {premium:.2f}")
        else:
            total_cost = 2000 + (age - profile["age"]) * 100
            if insurance_type == "Employer":
                oop = total_cost * 0.15
                premium = 1500 + (age - profile["age"]) * 40
            elif insurance_type == "Marketplace":
                oop = total_cost * 0.2
                premium = 1800 + (age - profile["age"]) * 60
            else:  # Uninsured
                oop = total_cost * 0.5
                premium = 0

        entry = {
            "Age": age,
            "Healthcare Cost": total_cost,
            "OOP": oop,
            "Premium": premium
        }
        cost_data.append(entry)

    return pd.DataFrame(cost_data)

def simulate_investment_strategy(cost_df, strategy=None):
    df = cost_df.copy()

    # Extract user-defined surplus and capital care allocation
    total_surplus = st.session_state.get("calculated_surplus", 0.0)
    capital_care_alloc = st.session_state.get("capital_care_alloc", 0.0)  # e.g., 0.3 = 30%
    reallocated_premium = st.session_state.get("reallocated_premium", 0.0)
    eligible_for_reallocation = st.session_state.get("eligible_for_reallocation", False)

    # Extract investment strategy rates and allocations
    short_rate = st.session_state.get("short_term_rate", 0.02)
    mid_rate = st.session_state.get("mid_term_rate", 0.05)
    long_rate = st.session_state.get("long_term_rate", 0.07)

    short_alloc = st.session_state.get("short_term_alloc", 0.2)
    mid_alloc = st.session_state.get("mid_term_alloc", 0.3)
    long_alloc = st.session_state.get("long_term_alloc", 0.5)

    # Calculate blended growth rate
    blended_growth = (
        short_rate * short_alloc +
        mid_rate * mid_alloc +
        long_rate * long_alloc
    )

    # Capital investment simulation from surplus and premium reallocation
    surplus_contribution = total_surplus * capital_care_alloc
    premium_contribution = reallocated_premium if eligible_for_reallocation else 0.0
    annual_contribution = surplus_contribution + premium_contribution
    # Optionally store in session state for visibility
    st.session_state.capital_from_surplus = surplus_contribution
    st.session_state.capital_from_reallocation = premium_contribution
    st.session_state.total_capital_contribution = annual_contribution
    capital_fund_value = 0
    capital_used = []
    capital_balance = []
    income_available = []
    surplus_allocated = []

    for cost in df["Healthcare Cost"]:
        capital_fund_value = (capital_fund_value + annual_contribution) * (1 + blended_growth)
        used = min(capital_fund_value, cost)
        capital_fund_value -= used
        capital_used.append(used)
        capital_balance.append(capital_fund_value)

    df["Capital Used"] = capital_used
    df["Capital Fund Remaining"] = capital_balance

    # Export DataFrame for downstream rendering (full DataFrame, no chart rendering here)
    st.session_state.capital_graph_df = df

    return df


# --- AI Recommendation Section (to be called after simulation outputs are calculated) ---
def display_ai_recommendations(after_capital_strategy):
    """
    Display the AI recommendation section after simulation outputs.
    Requires `after_capital_strategy` DataFrame and Streamlit session state variables.
    """
    # --- Inserted chronic/high-risk recommendation logic ---
    profile = st.session_state.get("profile", {})
    health_status = profile.get("health_status", "healthy")
    insurance_type = profile.get("insurance_type", "None")
    free_cash = st.session_state.get("free_cash", 0)
    savings = st.session_state.get("current_savings", 0)
    underinsured = insurance_type in ["None", "Marketplace / Self-insured"]

    # Apply chronic/high-risk recommendation logic
    if health_status in ["chronic", "high_risk"]:
        if free_cash > 0 and savings > 0:
            if underinsured:
                st.success("🧠 Recommended Plan: Capital-Bridge Plan (for chronic users with free cash and savings)")
            else:
                st.success("🧠 Recommended Plan: Protection-First Plan (chronic user with adequate insurance)")
        elif savings > 0:
            st.success("🧠 Recommended Plan: Capital-First Plan (chronic user with savings but low income)")
        else:
            st.success("🧠 Recommended Plan: Capital-First Plan (chronic user with limited financial capacity)")
        return
    # --- End inserted logic ---
    st.markdown("### 🤖 Personalized Strategy Breakdown")


def simulate_capital_allocation(cost_df, strategy_allocation, initial_capital, monthly_contribution, fund_source,
                                pct_from_savings, base_surplus=None):
    updated_df = cost_df.copy()

    updated_df["Capital_Contribution"] = monthly_contribution * 12  # annualized
    updated_df["Total_Capital_Used"] = updated_df["Capital_Contribution"].cumsum() + (
        initial_capital * (pct_from_savings / 100)
    )

    # Add cumulative capital value
    capital_value = []
    running_total = initial_capital * (pct_from_savings / 100)
    for _ in range(len(updated_df)):
        running_total += monthly_contribution * 12
        capital_value.append(running_total)
    updated_df["Capital Fund Value"] = capital_value

    # Add placeholder breakdown by investment strategy
    for tier in ["Short-Term", "Mid-Term", "Long-Term"]:
        allocation_pct = strategy_allocation.get(tier.lower().replace("-", "_"), 0) / 100
        updated_df[f"{tier}_Allocated"] = updated_df["Capital_Contribution"] * allocation_pct

    # Compute final net surplus
    if base_surplus is not None:
        updated_df["Net Surplus After Capital"] = base_surplus + updated_df["Capital Fund Value"]
    else:
        updated_df["Net Surplus After Capital"] = updated_df["Capital Fund Value"] - updated_df["Healthcare Cost"]

    return updated_df

def simulate_full_investment_strategy(
    profile,
    net_income_annual,
    savings_rate,
    savings_growth,
    capital_allocations,
    growth_short,
    growth_mid,
    growth_long,
    contrib_401k_employee,
    contrib_401k_employer,
    growth_401k,
    partner_401k_contrib,
    partner_employer_401k_contrib
):
    years = profile.get("simulation_years", 40)

    # Initialize investment buckets
    short_term = []
    mid_term = []
    long_term = []

    value_short = profile.get("start_short_term", 0)
    value_mid = profile.get("start_mid_term", 0)
    value_long = profile.get("start_long_term", 0)

    for i in range(years):
        annual_savings = net_income_annual * savings_rate * ((1 + savings_growth) ** i)

        value_short *= (1 + growth_short)
        value_short += annual_savings * capital_allocations.get("short_term", 0)
        short_term.append(value_short)

        value_mid *= (1 + growth_mid)
        value_mid += annual_savings * capital_allocations.get("mid_term", 0)
        mid_term.append(value_mid)

        value_long *= (1 + growth_long)
        value_long += annual_savings * capital_allocations.get("long_term", 0)
        long_term.append(value_long)

    # --- USER 401(k) ---
    user_401k = []
    value_401k = profile.get("start_401k_user", 0)
    for i in range(years):
        value_401k *= (1 + growth_401k)
        value_401k += contrib_401k_employee + contrib_401k_employer
        user_401k.append(value_401k)

    # --- PARTNER 401(k) ---
    partner_401k = []
    if profile.get("family_status") == "family":
        value_partner_401k = profile.get("start_401k_partner", 0)
        for i in range(years):
            value_partner_401k *= (1 + growth_401k)
            value_partner_401k += partner_401k_contrib + partner_employer_401k_contrib
            partner_401k.append(value_partner_401k)
    else:
        partner_401k = [0] * years

    return {
        "short_term": short_term,
        "mid_term": mid_term,
        "long_term": long_term,
        "user_401k": user_401k,
        "partner_401k": partner_401k
    }