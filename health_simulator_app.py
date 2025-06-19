# Main Streamlit App

import streamlit as st
st.set_page_config(page_title="Health Strategy Simulator", layout="wide")
import json
import pandas as pd
from insurance_module import get_insurance_costs_over_time, get_base_oop, get_oop_correction_ratio, get_base_premium
from simulator_core import generate_costs, simulate_investment_strategy, simulate_capital_allocation
from recommendation_engine import generate_recommendation, recommend_insurance_strategy
from projected_health_risk import get_risk_insight, get_risk_trajectory
from family_risk_module import get_family_risk_summary
from high_risk_module import compute_high_risk_score
import matplotlib.pyplot as plt

#
# ----------------- TAB LAYOUT WITH ACCESS CONTROL -----------------

st.image("logo_capitalcare360.png", width=200)

# Access control
with st.sidebar:
    st.header("🔐 Beta Access")
    code = st.text_input("Enter beta access code:", type="password")
    if code != "HSS_Beta_2025v1!":
        st.stop()

# App Title (just after access control)
st.title("🧭 Health Strategy Simulator")

# Tabs block (immediately after title)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Welcome", "Step 1: Profile", "Step 2: Financials",
    "Step 3: Simulation", "Step 4: Recommendations", "📥 Save"
])

# --- Upload Previous Simulation ---
with st.expander("⬆️ Upload Previous Simulation", expanded=False):
    uploaded_file = st.file_uploader("Choose a file to upload", type="json")
    if uploaded_file is not None:
        session_data = json.load(uploaded_file)
        st.session_state.update(session_data)
        st.success("Previous simulation loaded successfully!")

    # Only show tabbed layout if access code is correct
    # (Tabs are now always defined; you may use code to restrict content rendering if needed)

    # -------- Step 1: Profile & Insurance --------
    with tab2:
        st.header("Step 1: Profile & Insurance")
        age = st.number_input("Age", 18, 85, 30)
        user_age = age  # Preserve original user age
        gender = st.selectbox("Gender", ["male", "female"])
        health_status = st.selectbox("Health Status", ["healthy", "chronic", "high_risk"])
        family_status = st.selectbox("Family Status", ["single", "family"])
        dependents = st.number_input("Number of Dependents", 0, 10, 0)

        # --- Updated Dependent Risk Capture ---
        dependent_ages = []
        dependent_health_statuses = []
        for i in range(dependents):
            col1, col2 = st.columns(2)
            dep_age = col1.number_input(f"Dependent #{i+1} Age", 0, 25, 5, key=f"dep_age_{i}")
            health = col2.selectbox(
                f"Dependent #{i+1} Health Status",
                ["healthy", "chronic", "high_risk"],
                key=f"dep_health_{i}"
            )
            dependent_ages.append(dep_age)
            dependent_health_statuses.append(health)
        st.session_state["dependent_ages"] = dependent_ages
        st.session_state["dependent_health_statuses"] = dependent_health_statuses
        # ℹ️ Note about dependent coverage age limit
        st.markdown("ℹ️ **Note:** Dependents are considered covered under family insurance until age 25. Coverage ends at 26, following standard U.S. insurance rules.")

        partner_age = None
        partner_health_status = None
        if family_status == "family":
            partner_age = st.number_input("Partner Age", 18, 85, 30)
            partner_health_status = st.selectbox("Partner Health Status", ["healthy", "chronic", "high_risk"])

        insurance_type = st.radio("Insurance Type", ["Employer-based", "Marketplace / Self-insured", "None"])

        from insurance_module import get_insurance_costs_over_time

        st.subheader("📄 Insurance Premium and OOP Setup")

        # Determine whether to use national averages or custom inputs for premiums and OOP
        use_avg_inputs = st.radio("Use national average insurance and OOP costs?", ["Yes", "No"], index=0)

        if use_avg_inputs == "Yes":
            # Lookup values using the insurance module
            profile = {
                "age": user_age,
                "gender": gender,
                "health_status": health_status,
                "family_status": family_status,
                "insurance_type": "ESI" if insurance_type == "Employer-based" else ("ACA" if insurance_type == "Marketplace / Self-insured" else "Uninsured")
            }
            # Use get_insurance_costs_over_time for all years
            num_years = 30  # Default, will be recalculated below after cost_df is available
            insurance_costs = get_insurance_costs_over_time(profile, num_years)
            premium_list = insurance_costs["premium"]
            # --- Use risk-adjusted OOP for year 1 ---
            insurance_type_key = "ACA" if insurance_type == "Marketplace / Self-insured" else "ESI"
            base_oop = get_base_oop(insurance_type_key, family_status)
            oop_correction = get_oop_correction_ratio(user_age, insurance_type_key, health_status)
            risk_adjusted_oop = base_oop * oop_correction
            # --- Begin revised ACA family premium estimate logic ---
            if insurance_type == "Marketplace / Self-insured":
                # Use ACA family logic: base premium * risk multiplier, do NOT multiply by number of adults/family
                base_premium = get_base_premium("ACA", "family")
                risk_multiplier = get_oop_correction_ratio(user_age, "ACA", health_status)
                estimated_employee_premium = base_premium * risk_multiplier
                employee_premium = estimated_employee_premium
            else:
                employee_premium = premium_list[0] if len(premium_list) > 0 else 0
            employer_premium = 0  # Explicitly ignore employer's contribution
            annual_oop = risk_adjusted_oop
        else:
            employee_premium = st.number_input("Employee Contribution ($/yr)", min_value=0, value=2000)
            employer_premium = st.number_input("Employer Contribution ($/yr)", min_value=0, value=6000 if insurance_type == "Employer-based" else 0)
            annual_oop = st.number_input("Estimated Annual OOP ($/yr)", min_value=0, value=4800)

        # Premium inflation rate (moved from Step 2)
        st.subheader("📈 Inflation Assumption")
        premium_inflation = st.slider("Annual Premium Growth (%)", 0, 10, 5, help="Applies to premiums and OOP") / 100

        # Restore care preferences if missing
        st.subheader("Care Preferences")
        with st.expander("🏥 Select Your Care Preferences", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                include_primary = st.checkbox("Primary Care", value=True)
                include_chronic = st.checkbox("Chronic Care", value=True)
                include_preventive = st.checkbox("Preventive Care", value=True)
                include_surgical = st.checkbox("Surgical Care", value=True)
                include_cancer = st.checkbox("Cancer Care", value=True)
            with col2:
                include_mental = st.checkbox("Mental Health", value=True)
                include_emergency = st.checkbox("Emergency Care", value=True)
                include_eol = st.checkbox("End-of-Life Care", value=True)
                include_maternity = st.checkbox("Maternity Care", value=True)
                include_pediatric = st.checkbox("Pediatric Care", value=True)
            care_prefs = {
                "include_primary": include_primary,
                "include_chronic": include_chronic,
                "include_preventive": include_preventive,
                "include_surgical": include_surgical,
                "include_cancer": include_cancer,
                "include_mental": include_mental,
                "include_emergency": include_emergency,
                "include_eol": include_eol,
                "include_maternity": include_maternity,
                "include_pediatric": include_pediatric
            }
            st.session_state.care_prefs = care_prefs

        if st.button("Run Step 1"):
            st.session_state.step1_submitted = True
            st.session_state.step2_submitted = False
            st.session_state.step3_submitted = False
            st.session_state.step4_submitted = False
            profile = {
                "age": user_age,
                "gender": gender,
                "health_status": health_status,
                "family_status": family_status,
                "num_dependents": dependents,
                "dependent_ages": dependent_ages,
                "partner_age": partner_age,
                "partner_health_status": partner_health_status
            }
            care_prefs = st.session_state.get("care_prefs", {})
            cost_df = generate_costs(profile, care_prefs)
            # --- Patch: Ensure Healthcare Cost fallback if needed ---
            if "Capital+OOP" not in cost_df.columns and "Healthcare Cost" not in cost_df.columns:
                cost_df["Healthcare Cost"] = cost_df.get("Total Healthcare", 0)

            # --- Begin Premium Correction/Adjustment Logic ---
            # Define correction_ratio (example structure, replace with actual lookup as needed)
            # This should be loaded/defined elsewhere or imported, here is a sample for illustration:
            correction_ratio = {
                "18-34": {"healthy": {"ESI": 1.0, "ACA": 1.1}, "chronic": {"ESI": 1.2, "ACA": 1.3}, "high_risk": {"ESI": 1.5, "ACA": 1.7}},
                "35-49": {"healthy": {"ESI": 1.1, "ACA": 1.2}, "chronic": {"ESI": 1.3, "ACA": 1.4}, "high_risk": {"ESI": 1.6, "ACA": 1.8}},
                "50-64": {"healthy": {"ESI": 1.2, "ACA": 1.3}, "chronic": {"ESI": 1.4, "ACA": 1.5}, "high_risk": {"ESI": 1.7, "ACA": 1.9}},
                "65+":   {"healthy": {"ESI": 1.0, "ACA": 1.0}, "chronic": {"ESI": 1.0, "ACA": 1.0}, "high_risk": {"ESI": 1.0, "ACA": 1.0}},
            }
            # Determine age bracket for correction
            def get_age_bracket(age):
                if age < 35:
                    return "18-34"
                elif age < 50:
                    return "35-49"
                elif age < 65:
                    return "50-64"
                else:
                    return "65+"
            # Map UI insurance_type to correction key
            insurance_map = {
                "Employer-based": "ESI",
                "Marketplace / Self-insured": "ACA",
                "None": "Uninsured"
            }
            # --- insurance_type_key assignment for Step 1 Calculation ---
            insurance_type_key = "ACA" if insurance_type == "Marketplace / Self-insured" else "ESI"
            # Medicare values for age 65+ (example, can make these user adjustable)
            medicare_employee_value = 1800
            medicare_employer_value = 0

            # For projection, use the number of years in cost_df and user's starting age
            n_years = len(cost_df)
            start_age = profile["age"]
            # Save base premiums for reference
            base_employee_premium = employee_premium
            base_employer_premium = employer_premium
            # --- Use insurance_module's premium_list/oop_list if available and user chose averages ---
            use_avg_inputs_bool = (use_avg_inputs == "Yes")
            # If using national averages, use risk-adjusted, non-inflated logic for year 1 and projections
            if use_avg_inputs_bool:
                def extend_to_length(lst, n):
                    if len(lst) >= n:
                        return lst[:n]
                    elif len(lst) == 0:
                        return [0] * n
                    else:
                        return lst + [lst[-1]] * (n - len(lst))
                if 'insurance_costs' not in locals() or len(premium_list) < n_years:
                    insurance_costs = get_insurance_costs_over_time(profile, n_years)
                    premium_list = insurance_costs["premium"]
                premiums = extend_to_length(premium_list, n_years)
                employer_premiums = [0] * n_years

                # --- Begin risk-adjusted OOP logic ---
                total_oop_over_time = []
                for year in range(n_years):
                    age_this_year = profile["age"] + year
                    # Only apply to user for now (ignore partner/dependents for this block)
                    base_oop = get_base_oop(insurance_type_key, family_status)
                    oop_correction = get_oop_correction_ratio(age_this_year, insurance_type_key, health_status)
                    oop = base_oop * oop_correction
                    total_oop_over_time.append(oop)
                cost_df["Premiums"] = premiums
                cost_df["Employer Premiums"] = employer_premiums
                cost_df["OOP Cost"] = total_oop_over_time
                cost_df["Healthcare Cost"] = cost_df["OOP Cost"] + cost_df["Premiums"]
            else:
                # Build premium projections with correction factors (legacy logic)
                employee_premiums = []
                employer_premiums = []
                # --- Ensure oop_pct is defined ---
                oop_pct = 0.25  # Default to 25% of medical costs if not otherwise defined
                for i in range(n_years):
                    age = start_age + i
                    # Correction only for ESI or ACA, not for "None"
                    if insurance_type_key in ["ESI", "ACA"]:
                        age_bracket = get_age_bracket(age)
                        health = health_status
                        correction = correction_ratio.get(age_bracket, {}).get(health, {}).get(insurance_type_key, 1.0)
                    else:
                        correction = 1.0
                    # Pre-65: use corrected, post-65: switch to Medicare if ESI
                    if age >= 65 and insurance_type_key == "ESI":
                        emp_prem = medicare_employee_value
                        emr_prem = medicare_employer_value
                    else:
                        emp_prem = base_employee_premium * ((1 + premium_inflation) ** i) * correction
                        emr_prem = base_employer_premium * ((1 + premium_inflation) ** i) * correction
                    employee_premiums.append(emp_prem)
                    employer_premiums.append(emr_prem)
                premiums = employee_premiums
                cost_df["Premiums"] = premiums
                cost_df["Employer Premiums"] = employer_premiums
                # OOP logic unchanged
                if oop_pct is not None:
                    cost_df["OOP Cost"] = cost_df["Healthcare Cost"] * oop_pct
                else:
                    cost_df["OOP Cost"] = [annual_oop * ((1 + premium_inflation) ** i) for i in range(len(cost_df))]
                cost_df["Healthcare Cost"] = cost_df["OOP Cost"] + cost_df["Premiums"]

            high_risk_score = compute_high_risk_score(profile)
            st.session_state["high_risk_score"] = high_risk_score
            family_member_trajectories = {}
            family_member_cost_factors = {}
            family_member_trajectories["User"] = get_risk_trajectory(user_age, profile["health_status"])
            family_member_cost_factors["User"] = 1.0 if profile["health_status"] == "healthy" else (
                1.5 if profile["health_status"] == "chronic" else 2.0)
            if partner_age is not None and partner_health_status is not None:
                family_member_trajectories["Partner"] = get_risk_trajectory(partner_age, partner_health_status)
                family_member_cost_factors["Partner"] = 1.0 if partner_health_status == "healthy" else (
                    1.5 if partner_health_status == "chronic" else 2.0)
            st.session_state["family_member_trajectories"] = family_member_trajectories
            st.session_state["family_member_cost_factors"] = family_member_cost_factors
            dependent_trajectories = {}
            for i, (dep_age, dep_health) in enumerate(zip(dependent_ages, dependent_health_statuses)):
                label = f"Dependent #{i+1}"
                trajectory = get_risk_trajectory(dep_age, dep_health)
                dependent_trajectories[label] = trajectory
            st.session_state["dependent_trajectories"] = dependent_trajectories
            if st.checkbox("📉 Show Family Member Risk Trajectories"):
                selected_members = st.multiselect(
                    "Select family members to include in the risk graph:",
                    options=["User", "Partner"],
                    default=["User", "Partner"]
                )
                fig, ax = plt.subplots(figsize=(10, 5))
                for member in selected_members:
                    if member in family_member_trajectories:
                        trajectory = family_member_trajectories[member]
                    else:
                        trajectory = st.session_state.get("dependent_trajectories", {}).get(member)
                    if member.startswith("Dependent"):
                        dep_index = int(member.split("#")[1]) - 1
                        start_age = dependent_ages[dep_index]
                    else:
                        start_age = profile["age"] if member == "User" else profile.get("partner_age")
                    if trajectory is not None and start_age is not None:
                        age_range = list(range(start_age, start_age + len(trajectory)))
                        ax.plot(age_range, trajectory, label=member)
                ax.set_title("Projected Health Risk for Family Members")
                ax.set_xlabel("Age")
                ax.set_ylabel("Risk Level")
                ax.set_ylim(0, 1.05)
                ax.legend()
                st.pyplot(fig)
            st.session_state.cost_df = cost_df
            st.session_state.profile = profile
            st.session_state.insurance_type = insurance_type
            # Save the year 1 (age 0) employee and employer premium for reporting and reallocation logic
            # Save first year premiums for reporting
            if use_avg_inputs_bool:
                st.session_state.employee_premium = premiums[0] if premiums else 0
                st.session_state.employer_premium = 0
            else:
                st.session_state.employee_premium = employee_premiums[0] if employee_premiums else 0
                st.session_state.employer_premium = employer_premiums[0] if employer_premiums else 0
            st.session_state.premium_inflation = premium_inflation
            first_year = 0
            st.markdown("### 📊 Year 1 Cost Breakdown:")
            st.markdown(f"- **Premium**: ${round(st.session_state.employee_premium):,}/yr (employee contribution)")
            if use_avg_inputs_bool:
                st.markdown(f"- **Out-of-Pocket (risk-adjusted):** ${round(cost_df['OOP Cost'].iloc[first_year]):,}/yr")
            else:
                st.markdown(f"- **Out-of-Pocket:** ${round(cost_df['OOP Cost'].iloc[first_year]):,}/yr")
            st.markdown(f"- **Total Year 1 Cost (estimated)**: ${round(cost_df['Healthcare Cost'].iloc[first_year]):,}")
            st.line_chart(cost_df.set_index("Age")["Healthcare Cost"])
            st.success("Step 1 complete.")
            from projected_health_risk import get_risk_trajectory

    # -------- Step 2: Financial Inputs --------
    with tab3:
        st.header("Step 2: Financial Inputs")
        if "age" in st.session_state and "health_status" in st.session_state:
            st.session_state["risk_trajectory"] = get_risk_trajectory(
                st.session_state.age,
                st.session_state.health_status
            )
        if "cost_df" in st.session_state and not st.session_state.get("step2_submitted"):
            cost_df = st.session_state.cost_df
            insurance_type = st.session_state.insurance_type
            profile = st.session_state.profile
            oop_first_year = round(cost_df["OOP Cost"].iloc[0], 2)
            premium_first_year = round(cost_df["Premiums"].iloc[0], 2)
            net_income_monthly = 0
            with st.form("finance_form"):
                st.markdown("### 💵 Income & Tax Estimation")
                monthly_income = st.number_input("Monthly Gross Income ($)", 0, value=5000)
                est_tax_rate = st.slider("Estimated Tax Rate (%)", 0.0, 50.0, 25.0) / 100
                # --- Partner income/inputs for family, after user income ---
                if family_status == "family":
                    monthly_income_partner = st.number_input("Partner Monthly Gross Income ($)", min_value=0, value=4000, key="monthly_income_partner")
                    est_tax_rate_partner = st.slider("Estimated Tax Rate for Partner (%)", 0, 50, 20, key="tax_rate_partner") / 100
                    net_income_monthly_partner = monthly_income_partner * (1 - est_tax_rate_partner)
                else:
                    net_income_monthly_partner = 0
                net_income_monthly_user = monthly_income * (1 - est_tax_rate)
                net_income_monthly = net_income_monthly_user + net_income_monthly_partner
                st.session_state.net_income_monthly = net_income_monthly
                st.session_state.net_income_monthly_partner = net_income_monthly_partner
                net_income_annual = net_income_monthly * 12
                income_growth = st.slider("Income Growth (%)", 0.0, 10.0, 2.0) / 100

                # --- Partner income/inputs for family ---
                if family_status == "family":
                    net_income_annual_partner = net_income_monthly_partner * 12
                    income_growth_partner = st.slider("Partner's Income Growth Rate (%)", 0.0, 10.0, 3.0) / 100
                # --- Collect actual monthly expense and debt inputs at the start of Step 2 ---
                monthly_expenses = st.number_input("Monthly Household Expenses ($)", min_value=0, value=16500)
                debt_monthly_payment = st.number_input("Monthly Debt Payments ($)", min_value=0, value=1500)
                st.markdown("### 🧾 Monthly Fixed Commitments")
                st.markdown("### 💾 Savings Profile")
                savings_start = st.number_input("Current Savings Balance ($)", 0, value=10000)
                savings_growth = st.slider("Expected Savings Growth (%)", 0.0, 10.0, 3.0) / 100
                annual_contrib = st.number_input("Annual Savings Contribution ($)", 0, value=3000)
                savings_goals = st.multiselect(
                    "What is your savings primarily for?",
                    ["Home", "Education", "Vacations", "Retirement", "Health", "Rainy Day"],
                    default=["Retirement", "Health"]
                )

                st.markdown("### 🏦 401(k) Contributions")
                start_401k_user = st.number_input("Your Starting 401(k) Balance ($)", min_value=0, value=0)

                if family_status == "family":
                    start_401k_partner = st.number_input("Partner's Starting 401(k) Balance ($)", min_value=0, value=0)

                # Store in profile
                profile["start_401k_user"] = start_401k_user
                if family_status == "family":
                    profile["start_401k_partner"] = start_401k_partner

                contrib_401k_employee = st.number_input(
                    "Annual Employee 401(k) Contribution ($)",
                    min_value=0,
                    value=4000
                )

                contrib_401k_employer = st.number_input(
                    "Annual Employer 401(k) Match ($)",
                    min_value=0,
                    value=2000
                )

                growth_401k = st.slider("401(k) Growth Rate (%)", 0.0, 10.0, 5.0) / 100


                if family_status == "family":

                    partner_401k_contrib = st.number_input(
                        "Partner's Annual 401(k) Contribution ($)",
                        min_value=0,
                        value=4000,
                        key="partner_401k_contrib"
                    )

                    partner_employer_401k_contrib = st.number_input(
                        "Partner's Annual Employer 401(k) Match ($)",
                        min_value=0,
                        value=2000,
                        key="partner_employer_401k_contrib"
                    )
                    partner_growth_401k = st.slider("Partner's 401(k) Growth Rate (%)", 0.0, 10.0, 5.0) / 100

                    profile["partner_growth_401k"] = partner_growth_401k
                else:
                    # Optional: clear any previous partner values if not family
                    st.session_state.pop("partner_401k_contrib", None)
                    st.session_state.pop("partner_employer_401k_contrib", None)




                submit2 = st.form_submit_button("Run Step 2")
            if submit2:
                years = len(cost_df)
                age = profile["age"]
                # --- Revised Retirement-aware income projection ---
                income_proj = []
                for i in range(years):
                    if i + age < 65:
                        income = net_income_annual * ((1 + income_growth) ** i)
                    else:
                        income = income_proj[64 - age] * 0.4 if 64 - age >= 0 else net_income_annual * 0.4
                    income_proj.append(income)

                # --- Partner income projection using new variables ---
                if family_status == "family":
                    income_proj_partner = []
                    for i in range(years):
                        age_i = profile["age"] + i  # user age this year
                        partner_age_i = partner_age + i  # partner's age this year
                        if partner_age_i < 65:
                            income = net_income_annual_partner * ((1 + income_growth_partner) ** i)
                        else:
                            pre_retirement_index = 65 - partner_age
                            if pre_retirement_index >= 0:
                                base_income = net_income_annual_partner * (
                                            (1 + income_growth_partner) ** pre_retirement_index)
                            else:
                                base_income = net_income_annual_partner
                            income = base_income * 0.4
                        income_proj_partner.append(income)
                else:
                    income_proj_partner = [0 for _ in range(years)]

                # --- Combined income projection ---
                combined_income_proj = [user + partner for user, partner in zip(income_proj, income_proj_partner)]
                # Store the combined projection in session state
                st.session_state.combined_income_proj = combined_income_proj
                savings_proj = []
                current = savings_start
                for i in range(years):
                    current *= (1 + savings_growth)
                    current += annual_contrib
                    savings_proj.append(current)
                # --- User 401(k) projection with contributions stopping at age 65 ---
                proj_401k = []
                user_age = profile.get("age", 30)
                value_401k = profile.get("start_401k_user", 0)
                for i in range(years):
                    current_age = user_age + i
                    if i == 0:
                        value_401k = profile.get("start_401k_user", 0)
                    if current_age <= 65:
                        value_401k += contrib_401k_employee + contrib_401k_employer
                    value_401k *= (1 + growth_401k)
                    proj_401k.append(value_401k)
                # --- Partner 401(k) projection with contributions stopping at age 65 (retirement cutoff) ---
                if family_status == "family":
                    proj_401k_partner = []
                    value_401k_partner = profile.get("start_401k_partner", 0)
                    partner_age = profile.get("partner_age", 65)
                    # Retrieve partner-specific growth rate if available, else fallback to user growth rate
                    growth_401k_partner = profile.get("partner_growth_401k", growth_401k)
                    for i in range(years):
                        current_age = partner_age + i
                        if i == 0:
                            value_401k_partner = profile.get("start_401k_partner", 0)
                        if current_age <= 65:
                            value_401k_partner += partner_401k_contrib + partner_employer_401k_contrib
                        value_401k_partner *= (1 + growth_401k_partner)
                        proj_401k_partner.append(value_401k_partner)
                    st.session_state.proj_401k_partner = proj_401k_partner
                st.session_state.monthly_income = monthly_income
                st.session_state.net_income_annual = net_income_annual
                st.session_state.income_growth = income_growth
                st.session_state.monthly_expenses = monthly_expenses
                st.session_state.debt_monthly_payment = debt_monthly_payment
                st.session_state.savings_start = savings_start
                st.session_state.savings_growth = savings_growth
                st.session_state.annual_contrib = annual_contrib
                st.session_state.savings_goals = savings_goals
                st.session_state.contrib_401k_employee = contrib_401k_employee
                st.session_state.contrib_401k_employer = contrib_401k_employer
                st.session_state.growth_401k = growth_401k
                st.session_state.income_proj = combined_income_proj
                st.session_state.income_proj_partner = income_proj_partner
                st.session_state.savings_proj = savings_proj
                st.session_state.proj_401k = proj_401k


                insurance_type = st.session_state.get("insurance_type", "")
                employee_premium = st.session_state.get("employee_premium", 0)


                monthly_expenses = st.session_state.get("monthly_expenses", 0)
                debt_monthly_payment = st.session_state.get("debt_monthly_payment", 0)

                # Calculate available cash: net_income_monthly (user+partner) - premiums - oop - household_expenses - debt_payments
                # Do NOT subtract any monthly savings amount here
                if insurance_type == "Marketplace / Self-insured":
                    available_cash = net_income_monthly - (premium_first_year / 12) - (oop_first_year / 12) - monthly_expenses - debt_monthly_payment
                elif insurance_type == "Employer":
                    available_cash = net_income_monthly - (employee_premium / 12) - (oop_first_year / 12) - monthly_expenses - debt_monthly_payment
                else:  # Uninsured
                    available_cash = net_income_monthly - (oop_first_year / 12) - monthly_expenses - debt_monthly_payment

                st.session_state.available_cash = max(0, available_cash)

                st.success(
                    f"💰 Estimated Available Cash (Post Premium + OOP): ${st.session_state.available_cash:,.0f}/month")

                st.session_state.step2_submitted = True  # <- MOVE HERE

            if "available_cash" in st.session_state:
                rounded_cash = round(st.session_state.available_cash, 2)

                if rounded_cash <= 0:
                    st.warning(
                        "⚠️ Your expenses may exceed your net income. Please review your household spending or debt to ensure you can fund healthcare and savings goals.")

    # -------- Step 3: Summary View --------
    with tab4:
        st.header("Step 3: Summary View")

        # Variable Definitions
        cost_df = st.session_state.get("cost_df", pd.DataFrame())
        years = len(cost_df)
        profile = st.session_state.get("profile", {})
        user_age = profile.get("age", 40)
        user_income_annual = st.session_state.get("net_income_annual", 80000)
        user_replace_pct = st.session_state.get("user_replace_pct", 85)
        user_pension = st.session_state.get("user_pension", None)
        retirement_start = 65

        years_range = list(range(user_age, user_age + years))

        # Build Curve
        user_retirement_need_curve = []
        for i in range(years):
            age_i = user_age + i
            if age_i >= retirement_start:
                income_need = user_income_annual * (user_replace_pct / 100)
                pension_val = user_pension if user_pension is not None else user_income_annual * 0.3
                user_retirement_need_curve.append(income_need - pension_val)
            else:
                user_retirement_need_curve.append(0)

        if st.session_state.get("step2_submitted") and not st.session_state.get("step3_submitted"):
            cost_df = st.session_state.get("cost_df", pd.DataFrame())
            income_proj = st.session_state.income_proj
            savings_proj = st.session_state.savings_proj
            proj_401k = st.session_state.proj_401k
            monthly_expenses = st.session_state.monthly_expenses
            debt_monthly_payment = st.session_state.debt_monthly_payment
            income_growth = st.session_state.income_growth
            years = len(cost_df)
            household = [monthly_expenses * 12 * ((1 + income_growth) ** i) for i in range(years)]
            debt = [debt_monthly_payment * 12 * ((1 + income_growth) ** i) for i in range(years)]
            premiums = cost_df["Premiums"].tolist()
            oop = cost_df["OOP Cost"].tolist()
            healthcare = [premiums[i] + oop[i] for i in range(years)]
            total_exp = [household[i] + debt[i] + healthcare[i] for i in range(years)]
            total_income = [income_proj[i] + savings_proj[i] for i in range(years)]
            surplus = [total_income[i] - total_exp[i] for i in range(years)]
            st.session_state.surplus = surplus
            df_compare = pd.DataFrame({
                "Age": cost_df["Age"],
                "Household Expenses": household,
                "Debt Payments": debt,
                "Premiums": premiums,
                "OOP": oop,
                "Total Healthcare": healthcare,
                "Total Expenses": total_exp,
                "Income + Savings": total_income,
                "Surplus/Deficit": surplus
            })
            st.session_state.step3_submitted = True
            st.session_state.expense_df = df_compare
            st.write("### 📊 Financial Overview by Age")
            st.dataframe(df_compare.set_index("Age"))
            st.write("### 📈 Surplus/Deficit vs. Income and Total Expenses")
            chart_data = df_compare.set_index("Age")[["Surplus/Deficit", "Total Expenses", "Income + Savings"]]
            st.line_chart(chart_data)
            st.write("### 🏥 Healthcare vs. Total Expenses")
            chart_health = df_compare.set_index("Age")[["Total Healthcare", "Total Expenses"]]
            st.line_chart(chart_health)


            # --- NEW: User and Partner 401(k) Growth Over Time ---
            st.markdown("### 🟩 User and Partner 401(k) Growth Over Time")
            # Use the projected 401k from st.session_state for the user
            ages = list(cost_df["Age"])
            user_401k = st.session_state.proj_401k if "proj_401k" in st.session_state else []
            # Partner 401k: reconstruct if available, else zeros
            profile = st.session_state.get("profile", {})
            family_status = profile.get("family_status", "single")
            # Partner 401k: use the stored projection from session state
            if family_status == "family":
                proj_401k_partner = st.session_state.get("proj_401k_partner", [0] * years)
                partner_401k = proj_401k_partner
            else:
                partner_401k = [0] * len(ages)
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(ages, user_401k, label="User 401(k)", color="green", linewidth=2)
            if any(p > 0 for p in partner_401k):
                ax.plot(ages, partner_401k, label="Partner 401(k)", color="blue", linewidth=2)
            ax.set_title("User and Partner 401(k) Growth Over Time")
            ax.set_xlabel("Age")
            ax.set_ylabel("401(k) Balance ($)")
            ax.legend()
            st.pyplot(fig)


            # -------- Retirement Income Coverage: UI Inputs --------
            st.markdown("### 📉 Retirement Income Coverage")
            st.markdown("Visualize how your 401(k), savings, and pension help meet income needs in retirement.")

            with st.expander("🎯 Post-Retirement Income Replacement Goals"):
                st.markdown("Estimate how much of your income you’ll need annually after retirement.")

                st.subheader("User Retirement Planning")
                user_replace_pct = st.slider("Desired Income Replacement % (User)", 50, 100, 85, step=5)
                st.session_state["user_replace_pct"] = user_replace_pct
                user_knows_pension = st.radio("Do you know your expected pension? (User)", ["Yes", "No"], key="user_pension_toggle")
                if user_knows_pension == "Yes":
                    user_pension = st.number_input("Annual Pension Amount (User)", min_value=0, value=20000)
                else:
                    user_pension = None
                st.session_state["user_pension"] = user_pension

                if st.session_state.get("profile", {}).get("family_status") == "family":
                    st.subheader("Partner Retirement Planning")
                    partner_replace_pct = st.slider("Desired Income Replacement % (Partner)", 50, 100, 85, step=5)
                    st.session_state["partner_replace_pct"] = partner_replace_pct
                    partner_knows_pension = st.radio("Do you know your expected pension? (Partner)", ["Yes", "No"], key="partner_pension_toggle")
                    if partner_knows_pension == "Yes":
                        partner_pension = st.number_input("Annual Pension Amount (Partner)", min_value=0, value=20000)
                    else:
                        partner_pension = None
                    st.session_state["partner_pension"] = partner_pension
                else:
                    partner_replace_pct = 0
                    partner_pension = None


            st.subheader("📈 401(k) Coverage vs. Retirement Needs")
            fig, ax = plt.subplots()
            years_range = list(range(age, age + years))
            retirement_start = 65  # Or st.session_state.get("retirement_age", 65) if it's dynamic
            user_retirement_need_curve = []
            for i in range(years):
                age_i = user_age + i
                if age_i >= retirement_start:
                    income_need = user_income_annual * (user_replace_pct / 100)
                    pension_val = user_pension if user_pension is not None else user_income_annual * 0.3
                    user_retirement_need_curve.append(income_need - pension_val)
                else:
                    user_retirement_need_curve.append(0)
            coverage_values_partner = [st.session_state.get("coverage_401k_partner", 0)] * years



            ax.plot(years_range, proj_401k, label="User 401(k)", linestyle='--')
            ax.plot(years_range, user_retirement_need_curve, label="User Retirement Need (net)")
            if family_status == "family":
                ax.plot(years_range, proj_401k_partner, label="Partner 401(k)", linestyle='--')
                ax.plot(years_range, [st.session_state.get("coverage_401k_partner", 0)] * years, label="Partner Retirement Need (85%)")
            ax.set_xlabel("Age")
            ax.set_ylabel("401(k) Balance ($)")
            ax.set_title("401(k) vs. Retirement Income Target")
            ax.legend()
            st.pyplot(fig)

            # -------- Retirement Income Coverage: Gap and Drawdown Logic --------
            # --- Setup variables ---
            profile = st.session_state.get("profile", {})
            user_age = profile.get("age", 40)
            partner_age = profile.get("partner_age", 38)
            family_status = profile.get("family_status", "individual")
            user_income_annual = st.session_state.get("net_income_annual", 80000)
            partner_income_annual = st.session_state.get("net_income_annual_partner", 60000)
            user_401k_balance = profile.get("start_401k_user", 0)
            partner_401k_balance = profile.get("start_401k_partner", 0) if family_status == "family" else 0
            total_savings = st.session_state.get("savings_start", 0)

            if "cost_df" in st.session_state and "Year" in st.session_state.cost_df.columns:
                cost_df = st.session_state.get("cost_df", pd.DataFrame())
            else:
                cost_df = pd.DataFrame({"Year": [2025 + i for i in range(50)]})

            years = len(cost_df)
            retirement_start = 65

            # --- Income gap calculation ---
            income_replacement = []
            for i in range(years):
                age = user_age + i
                total_gap = 0

                if age >= retirement_start:
                    user_income_need = user_income_annual * (user_replace_pct / 100)
                    user_pension_val = user_pension if user_pension is not None and user_pension > 0 else user_income_annual * 0.3
                    user_gap = max(0, user_income_need - user_pension_val)

                    if family_status == "family":
                        partner_age_i = partner_age + i
                        if partner_age_i >= retirement_start:
                            partner_income_need = partner_income_annual * (partner_replace_pct / 100)
                            partner_pension_val = partner_pension if partner_pension is not None and partner_pension > 0 else partner_income_annual * 0.3
                            partner_gap = max(0, partner_income_need - partner_pension_val)
                        else:
                            partner_gap = 0
                    else:
                        partner_gap = 0

                    # --- DEBUG BLOCK: Show year-by-year gap calculation values (USER ONLY) ---
                    st.write({
                        "year": cost_df["Year"].iloc[i] if "Year" in cost_df.columns else f"Year {i}",
                        "user_income_annual": user_income_annual,
                        "user_replace_pct": user_replace_pct,
                        "user_income_need": user_income_need,
                        "user_pension_val": user_pension_val,
                        "user_gap": user_gap
                    })

                    total_gap = user_gap + partner_gap

                income_replacement.append(total_gap)

            # --- Drawdown logic ---
            remaining_401k = user_401k_balance + partner_401k_balance
            remaining_savings = total_savings

            drawdown_401k = []
            drawdown_savings = []
            income_deficit = []

            for gap in income_replacement:
                draw_401k = min(gap, remaining_401k)
                remaining_401k -= draw_401k

                draw_sav = max(0, min(gap - draw_401k, remaining_savings))
                remaining_savings -= draw_sav

                deficit = max(0, gap - draw_401k - draw_sav)

                drawdown_401k.append(draw_401k)
                drawdown_savings.append(draw_sav)
                income_deficit.append(deficit)

            # -------- Retirement Income Coverage: Output --------
            # --- Output DataFrame ---
            cost_df["Year"] = cost_df["Year"].astype(int)
            income_df = pd.DataFrame({
                "Year": cost_df["Year"],
                "Retirement Income Need": income_replacement,
                "Covered by 401(k)": drawdown_401k,
                "Covered by Savings": drawdown_savings,
                "Uncovered Deficit": income_deficit,
            })

            retirement_view = income_df[income_df["Retirement Income Need"] > 0]

            st.line_chart(retirement_view.set_index("Year")[[
                "Retirement Income Need",
                "Covered by 401(k)",
                "Covered by Savings",
                "Uncovered Deficit"
            ]])

            with st.expander("🔎 View Year-by-Year Table (Retirement Only)"):
                st.dataframe(retirement_view)

            # Store in session for download or reuse
            st.session_state["retirement_income_coverage"] = income_df

    # -------- Step 4: Recommendations --------
    with tab5:
        st.header("Step 4: Recommendations")
        # --- Adjust 401(k) and savings based on retirement drawdown ---
        ret_coverage = st.session_state.get("retirement_income_coverage")
        if ret_coverage is not None and not ret_coverage.empty:
            total_401k_used = ret_coverage["Covered by 401(k)"].sum()
            total_savings_used = ret_coverage["Covered by Savings"].sum()

            original_user_401k = st.session_state.get("profile", {}).get("start_401k_user", 0)
            original_partner_401k = st.session_state.get("profile", {}).get("start_401k_partner", 0)
            original_savings = st.session_state.get("savings_start", 0)

            # Remaining capital after income replacement
            adjusted_401k = max(0, original_user_401k + original_partner_401k - total_401k_used)
            adjusted_savings = max(0, original_savings - total_savings_used)

            st.session_state["available_401k_after_retirement"] = adjusted_401k
            st.session_state["available_savings_after_retirement"] = adjusted_savings

        # --- Retirement Income Strategy Prompt ---
        st.markdown("#### 🎯 Retirement Income Strategy")
        # Insert post-retirement income replacement goal prompt
        st.markdown("#### 🧮 Post-Retirement Income Replacement Goal")
        income_replacement_ratio = st.slider("What percentage of your pre-retirement income do you aim to replace?", min_value=50, max_value=100, value=85, step=5) / 100
        assumed_social_security_ratio = 0.40
        gap_ratio = max(0, income_replacement_ratio - assumed_social_security_ratio)

        # Retrieve projections and profile
        proj_401k = st.session_state.get("proj_401k", [])
        proj_401k_partner = st.session_state.get("proj_401k_partner", [])
        income_proj = st.session_state.get("income_proj", [])
        income_proj_partner = st.session_state.get("income_proj_partner", [])
        profile = st.session_state.get("profile")
        family_status = profile.get("family_status", "single") if profile else "single"
        user_age = profile.get("age", 40) if profile else 40
        partner_age = profile.get("partner_age", 40) if (profile and family_status == "family") else None
        net_income_annual = st.session_state.get("net_income_annual", 0)

        # Calculate last year pre-retirement income from combined income projection
        pre_retirement_index = 64 - user_age
        final_income_user = income_proj[pre_retirement_index] if pre_retirement_index >= 0 and len(income_proj) > pre_retirement_index else net_income_annual
        final_income_partner = income_proj_partner[pre_retirement_index] if family_status == "family" and pre_retirement_index >= 0 and len(income_proj_partner) > pre_retirement_index else 0
        combined_final_income = final_income_user + final_income_partner

        # Set target coverage need
        coverage_needed = combined_final_income * gap_ratio
        st.session_state["coverage_401k_user"] = coverage_needed

        st.markdown("How much of your 401(k) should be allocated to cover your **retirement income gap**?")
        percent_401k_allocation = st.slider("Select % to allocate:", 0, 100, int(income_replacement_ratio * 100))
        st.session_state["401k_retirement_allocation"] = percent_401k_allocation

        # 401(k) coverage recommendation logic
        if "proj_401k" in st.session_state and "coverage_401k_user" in st.session_state:
            if st.session_state["proj_401k"] and st.session_state["proj_401k"][-1] >= st.session_state["coverage_401k_user"]:
                st.success("✅ Your 401(k) balance is projected to cover your retirement income needs.")
            else:
                st.warning("⚠️ Your 401(k) may not fully cover your retirement income gap.")
        surplus = st.session_state.get("surplus")
        cost_df = st.session_state.get("cost_df", pd.DataFrame())
        insurance_type = st.session_state.get("insurance_type", "None")
        # Removed free cash display in Step 4 as per revert request
        if surplus is not None and cost_df is not None and profile is not None:
            st.markdown("### 📊 Surplus vs. Cost Analysis")
            # Ensure all series are trimmed to the minimum common length to avoid mismatched lengths
            min_len = min(len(cost_df["Age"]), len(surplus), len(cost_df["Healthcare Cost"]))
            chart_df = pd.DataFrame({
                "Age": cost_df["Age"][:min_len],
                "Surplus": surplus[:min_len],
                "Healthcare Cost": cost_df["Healthcare Cost"][:min_len]
            }).set_index("Age")
            st.markdown("✅ Rendered surplus vs. cost chart")
            st.line_chart(chart_df)
            if "family_member_trajectories" in st.session_state:
                st.markdown("### 📉 Projected Health Risk Over Time")
                fig, ax = plt.subplots(figsize=(10, 4))
                critical_ages = {}
                for member in ["User", "Partner"]:
                    if member in st.session_state["family_member_trajectories"]:
                        trajectory = st.session_state["family_member_trajectories"][member]
                        start_age = profile["age"] if member == "User" else profile.get("partner_age")
                        if start_age is None:
                            continue
                        age_range = list(range(start_age, start_age + len(trajectory)))
                        ax.plot(age_range, trajectory, linewidth=2, label=f"{member} Risk")
                        try:
                            crit_idx = next(i for i, val in enumerate(trajectory) if val >= 0.9)
                            critical_ages[member] = age_range[crit_idx]
                            ax.axvline(x=age_range[crit_idx], linestyle="--", label=f"{member} Critical Age: {age_range[crit_idx]}")
                        except StopIteration:
                            pass
                ax.set_xlabel("Age")
                ax.set_ylabel("Risk Level")
                ax.set_ylim([0, 1.05])
                ax.set_title("Projected Health Risk Trajectories")
                ax.legend()
                st.pyplot(fig)
            total_annual_premium = st.session_state.get("employee_premium", 0) + st.session_state.get("employer_premium", 0)
            total_monthly_premium = total_annual_premium / 12
            virtual_primary_cost = 80
            surgical_bundle_avg = 100
            eye_dental_addon = 50
            benchmark_monthly = virtual_primary_cost + surgical_bundle_avg + eye_dental_addon
            if total_monthly_premium > benchmark_monthly:
                st.info(f"💡 You are currently paying **${total_monthly_premium:.0f}/mo** in premiums. "
                        f"Based on typical digital-first + bundle alternatives (~${benchmark_monthly}/mo), "
                        "you may be overpaying. Consider reallocating the difference into a long-term health fund.")
                st.session_state["suggest_reallocation"] = True
            else:
                st.session_state["suggest_reallocation"] = False
            submit4 = st.button("Generate AI Recommendations")
            if submit4:
                try:
                    st.success("✅ Submit button clicked")
                    st.session_state.step4_submitted = True
                    # Ensure surplus is a list for generate_recommendation
                    surplus = st.session_state.get("surplus", [])
                    if isinstance(surplus, float):
                        surplus = [surplus]
                    cost_df = st.session_state.get("cost_df", pd.DataFrame())
                    profile = st.session_state.profile
                    insurance_type = st.session_state.get("insurance_type", "None")
                    capital_invest_toggle = st.session_state.get("capital_invest_toggle", "No")
                    recs = generate_recommendation(
                        profile=profile,
                        insurance_type=insurance_type,
                        surplus=[st.session_state.get("surplus", 0)],
                        capital_strategy=st.session_state.get("cap_alloc", {}),
                        risk_trajectory=st.session_state.get("risk_trajectory", []),
                        family_risk_summary=st.session_state.get("family_risk_summary", {}),
                        high_risk_score=st.session_state.get("high_risk_score")
                    )
                    insurance_rec = {}
                    if capital_invest_toggle == "No":
                        annual_surplus = surplus[-1] if isinstance(surplus, list) else surplus
                        capital_shift = st.session_state.get("capital_shift", 0)
                        insurance_rec = recommend_insurance_strategy(
                            profile=profile,
                            surplus=annual_surplus,
                            insurance_type=insurance_type,
                            capital_shift=capital_shift
                        )
                        if isinstance(insurance_rec, dict):
                            for key, value in insurance_rec.items():
                                recs.append(f"📌 {key}: {value}")
                        elif isinstance(insurance_rec, str):
                            recs.append(f"📌 {insurance_rec}")
                    risk_insight = get_risk_insight(profile["age"], profile["health_status"])
                    if risk_insight:
                        recs.append("🧠 " + risk_insight)
                    st.session_state.recs = recs
                    st.session_state.insurance_rec = insurance_rec
                    st.session_state.risk_insight = risk_insight
                except Exception as e:
                    st.error(f"❌ Exception occurred: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        if st.session_state.get("step4_submitted"):
            profile = st.session_state.get("profile", {})
            insurance_type = st.session_state.get("insurance_type", "None")
            cost_df = st.session_state.get("cost_df", None)
            st.subheader("📌 General Recommendation")
            st.markdown("✅ Displayed general recommendations")
            if st.session_state.get("risk_insight"):
                st.markdown(f"🧠 {st.session_state['risk_insight']}")
            recs = st.session_state.get("recs", [])
            st.subheader("🧭 Personalized Recommendations")
            if recs:
                for rec in recs:
                    if "📌 capital shift" in rec.lower() or "capital_shift" in rec.lower():
                        continue
                    st.markdown(f"- {rec}")
            else:
                st.markdown("No personalized recommendations to display.")
            # --- Display monthly premium and OOP using synced logic with Step 1 ---
            employee_premium = st.session_state.get("employee_premium", 0)
            cost_df = st.session_state.get("cost_df")
            if cost_df is not None and len(cost_df) > 0:
                monthly_premium = employee_premium / 12
                monthly_oop = cost_df["OOP Cost"].iloc[0] / 12
                st.markdown(f"**Your estimated monthly premium** (based on Year 1): ${round(monthly_premium):,}")
                st.markdown(f"**Your estimated monthly OOP** (based on Year 1): ${round(monthly_oop):,}")
            st.subheader("🧮 Capital Strategy Options")
            st.markdown("### Option 1: 💰 Allocate Funds from Savings or Income")
            st.markdown("This section helps you decide how to allocate available funds to your capital care fund.")
            # --- Funding source selection with conditional inputs ---
            fund_source = st.radio("Choose source of capital:", ["From Existing Savings", "From Monthly Income"])
            st.session_state.capital_fund_source = fund_source
            if fund_source == "From Existing Savings":
                # Use available_savings_after_retirement if available, else fallback to savings_start
                available_savings = st.session_state.get("available_savings_after_retirement", st.session_state.get("savings_start", 0))
                st.markdown(f"💡 Savings available after retirement drawdown: ${available_savings:,.0f}")
                allocate_pct = st.slider("% of Current Savings to Allocate", 0, 100, 0)
                st.session_state.capital_savings_pct = allocate_pct
            elif fund_source == "From Monthly Income":
                monthly_contrib = st.number_input("Monthly Contribution to Capital Health Fund ($)", min_value=0, value=0)
                st.session_state.capital_monthly_contrib = monthly_contrib
                # --- Real-time Estimated Free Cash Calculation ---
                monthly_income = st.session_state.get("monthly_income", 0)
                monthly_expenses = st.session_state.get("monthly_expenses", 0)
                monthly_debt = st.session_state.get("debt_monthly_payment", 0)
                employee_premium = st.session_state.get("employee_premium", 0)
                monthly_premium = employee_premium / 12 if employee_premium else 0
                estimated_free_cash = st.session_state.get("available_cash", 0)
                st.markdown(f"💡 Estimated Free Cash: ${estimated_free_cash:,.0f}/month")
            # 🔒 Determine long-term capital lock period based on age
            age = st.session_state.profile["age"]
            if age < 30:
                long_term_lock_years = 30
            elif age < 40:
                long_term_lock_years = 20
            elif age < 50:
                long_term_lock_years = 10
            else:
                long_term_lock_years = 5
            st.session_state.long_term_lock_years = long_term_lock_years
            st.markdown(
                f"📌 Note: Based on your age, long-term capital is assumed to be locked for <strong>{long_term_lock_years} years</strong> (aligned with 401(k)/pension rules).",
                unsafe_allow_html=True
            )
            st.markdown("---")
            st.markdown("### Option 2: 🔄 Reallocate Insurance Premiums")
            st.markdown("Consider replacing current insurance with digital-first services and surgery bundles.")
            st.markdown("### 🩺 Projected Digital-First Healthcare Costs vs Current Premiums")
            st.markdown("""
            ### 🏥 Care Platform Comparison

            | Provider           | Services Included                                | Est. Monthly Cost     |
            |--------------------|--------------------------------------------------|------------------------|
            | **Mira**           | Urgent care, labs, prescriptions                 | $45–$80               |
            | **One Medical**    | Virtual + in-person care, pediatrics             | $199/year + insurance |
            | **Amazon Clinic**  | 24/7 virtual primary care                        | ~$75                  |
            | **K Health**       | Primary + mental health + urgent care            | $49–$79               |
            | **Teladoc**        | General, mental, dermatology                     | $0–$75 per visit      |
            | **Christus Virtual** | Primary care in Texas/Southeast               | $45                   |
            """)
            st.markdown("### 📊 Projected Costs")
            st.markdown("- **Virtual Primary Care Estimate**: $80/mo")
            st.markdown("- **Surgery Bundle Average**: $100/mo")
            st.markdown("- **Vision/Dental Add-On**: $50/mo")
            total_estimate = 80 + 100 + 50
            current_premium = st.session_state.get("employee_premium", 0) + st.session_state.get("employer_premium", 0)
            delta = current_premium / 12 - total_estimate
            if delta > 0:
                st.success(f"Estimated monthly savings from reallocation: ${delta:.0f}")
            else:
                st.info("Your current premiums are comparable to digital-first alternatives.")
            capital_invest_toggle = st.selectbox(
                "Do you want to evaluate how a dedicated Capital Care Investment strategy can help you meet your objectives?",
                ["No", "Yes"],
                key="capital_invest_toggle"
            )

            if capital_invest_toggle == "Yes":
                st.markdown("#### 💼 Capital Investment Strategy")
                st.markdown("Adjust how you'd distribute your capital care investment:")

                short_term = st.slider("Short-Term (%)", 0, 100, 20, key="short_term")
                mid_term = st.slider("Mid-Term (%)", 0, 100 - short_term, 30, key="mid_term")
                long_term = 100 - short_term - mid_term
                st.write(f"Long-Term: {long_term}%")

                st.session_state.cap_alloc = {
                    "short": short_term / 100,
                    "mid": mid_term / 100,
                    "long": long_term / 100
                }

                # Capital growth input defaults (could be made user adjustable)
                capital_growth_inputs = {
                    "short": 0.03,
                    "mid": 0.05,
                    "long": 0.07
                }

                # --- Age-based lock period function ---
                def get_long_term_lock_years(user_age):
                    if user_age < 30:
                        return 30
                    elif user_age < 40:
                        return 20
                    elif user_age < 50:
                        return 15
                    elif user_age < 60:
                        return 10
                    else:
                        return 5

                # Button to run capital investment strategy
                if st.button("Run Capital Investment Strategy"):
                    # --- Capital Investment Inputs Setup ---
                    cost_df = st.session_state.cost_df
                    # Use available_savings_after_retirement if available, else fallback to savings_start
                    current_savings = st.session_state.get("current_savings", st.session_state.get("available_savings_after_retirement", st.session_state.get("savings_start", 0)))
                    fund_source = st.session_state.get("capital_fund_source", "Select One")
                    # Use new funding logic for initial_capital
                    if fund_source == "From Existing Savings":
                        savings_pct = st.session_state.get("capital_savings_pct", 0)
                        initial_capital = current_savings * savings_pct / 100
                        monthly_contribution = 0
                    elif fund_source == "From Monthly Income":
                        monthly_contribution = st.session_state.get("capital_monthly_contrib", 0)
                        initial_capital = monthly_contribution * 12
                        savings_pct = 0
                    else:
                        initial_capital = 0
                        monthly_contribution = 0
                        savings_pct = 0

                    # --- Add premium reallocation savings if applicable ---
                    # Include premium reallocation savings if applicable
                    delta = st.session_state.get("employee_premium", 0) + st.session_state.get("employer_premium", 0)
                    delta = delta / 12 - 230  # 230 is the benchmark (80 + 100 + 50)
                    if st.session_state.get("suggest_reallocation", False) and delta > 0:
                        premium_savings = delta
                    else:
                        premium_savings = 0

                    # Combine with Option 1
                    monthly_contribution += premium_savings

                    # --- Age-based lock period for long-term capital ---
                    user_age = st.session_state.profile["age"]
                    lock_years = get_long_term_lock_years(user_age)

                    # Info note about long-term lock years
                    st.markdown(f"⚠️ **Note**: Long-term capital funds are protected for your future. Based on your age ({user_age}), these become available after **{lock_years} years** — similar to pensions or 401(k) accounts.")

                    capital_sim_results = simulate_capital_allocation(
                        cost_df=cost_df,
                        strategy_allocation=st.session_state.cap_alloc,
                        initial_capital=initial_capital,
                        monthly_contribution=monthly_contribution,
                        fund_source=fund_source,
                        pct_from_savings=savings_pct
                    )

                    st.session_state["capital_sim_results"] = capital_sim_results

                    # Display chart if simulation ran
                    if capital_sim_results is not None and not capital_sim_results.empty:
                        # --- Show only Capital Fund Value line chart before new vesting chart ---
                        if "Capital Fund Value" in capital_sim_results.columns:
                            st.markdown("### 💹 Total Capital Care Savings Over Time")
                            st.line_chart(
                                capital_sim_results[["Capital Fund Value"]],
                                use_container_width=True
                            )

                        # --- Insert Capital Care: Total vs. Available Funds Comparison Chart ---
                        if all(col in capital_sim_results.columns for col in ["Capital Fund Value", "Short-Term_Allocated", "Mid-Term_Allocated", "Long-Term_Allocated"]):
                            # --- Compute Vested Capital from Allocations with Rolling Vesting ---
                            available_capital_vested = []
                            capital_sim_results[
                                ["Short-Term_Allocated", "Mid-Term_Allocated", "Long-Term_Allocated"]].head(10)
                            short_vested_list = []
                            mid_vested_list = []
                            long_vested_list = []

                            start_age = profile.get("age", 30)
                            short_rate = 0.03
                            mid_rate = 0.05
                            long_rate = 0.07

                            for i in range(len(capital_sim_results)):
                                short_vested = 0
                                mid_vested = 0
                                long_vested = 0

                                if i >= 2:
                                    short_vested = sum([
                                        capital_sim_results["Short-Term_Allocated"].iloc[j] * ((1 + short_rate) ** (i - j))
                                        for j in range(i - 2, i + 1)
                                    ])
                                else:
                                    short_vested = sum([
                                        capital_sim_results["Short-Term_Allocated"].iloc[j] * ((1 + short_rate) ** (i - j))
                                        for j in range(0, i + 1)
                                    ])

                                if i >= 5:
                                    mid_vested = sum([
                                        capital_sim_results["Mid-Term_Allocated"].iloc[j] * ((1 + mid_rate) ** (i - j))
                                        for j in range(i - 5, i + 1)
                                    ])
                                else:
                                    mid_vested = sum([
                                        capital_sim_results["Mid-Term_Allocated"].iloc[j] * ((1 + mid_rate) ** (i - j))
                                        for j in range(0, i + 1)
                                    ])

                                if (start_age + i) >= 65:
                                    long_vested = sum([
                                        capital_sim_results["Long-Term_Allocated"].iloc[j] * ((1 + long_rate) ** (i - j))
                                        for j in range(0, i + 1)
                                    ])

                                short_vested_list.append(short_vested)
                                mid_vested_list.append(mid_vested)
                                long_vested_list.append(long_vested)
                                available_capital_vested.append(short_vested + mid_vested + long_vested)

                            # Debug output
                            debug_df = pd.DataFrame({
                                "Short-Term Vested": short_vested_list,
                                "Mid-Term Vested": mid_vested_list,
                                "Long-Term Vested": long_vested_list,
                                "Total Vested Capital": available_capital_vested
                            })
                            st.markdown("### 🧪 Debug: Vested Capital Breakdown")
                            st.dataframe(debug_df)

                            # Fallback warning if all vested capital entries are zero
                            if all(v == 0 for v in available_capital_vested):
                                st.warning("⚠️ No capital allocations detected for vesting. Please review your input values.")

                        capital_summary_df = pd.DataFrame({
                            "Total Capital Care Savings": capital_sim_results["Capital Fund Value"],
                            "Available Capital (Vested)": available_capital_vested
                        }, index=capital_sim_results.index)

                        st.markdown("### 💰 Capital Care: Total vs. Available Funds")
                        st.line_chart(capital_summary_df, use_container_width=True)

                        st.markdown("### 📈 Capital Investment Strategy Outcome")

                        profile = st.session_state.get("profile", {})
                        ages = capital_sim_results.index + profile.get("age", 30)
                        income_savings = st.session_state.expense_df["Income + Savings"]
                        after_capital_strategy = capital_sim_results["Capital Fund Value"]
                        combined = [income_savings[i] + after_capital_strategy[i] for i in range(len(income_savings))]

                        df_plot = pd.DataFrame({
                            "Age": ages,
                            "Income + Savings": income_savings,
                            "Healthcare Expenses": st.session_state.expense_df["Total Healthcare"],
                            "Total Expenses": st.session_state.expense_df["Total Expenses"],
                            "Capital Care Savings ($)": after_capital_strategy,
                            "Total Resources (Capital Care + Income + Savings)": combined
                        }).set_index("Age")

                        st.line_chart(df_plot, use_container_width=True)

                        st.markdown("### 💡 401(k) Coverage Insights")
                        if st.session_state["proj_401k"][-1] >= st.session_state["coverage_401k_user"]:
                            st.success("User’s 401(k) is on track to cover 85% of their final pre-retirement income.")
                        else:
                            st.warning("User’s 401(k) may fall short of covering 85% of retirement needs.")

                        if family_status == "family":
                            if st.session_state["proj_401k_partner"][-1] >= st.session_state["coverage_401k_partner"]:
                                st.success(
                                    "Partner’s 401(k) is on track to cover 85% of their final pre-retirement income.")
                            else:
                                st.warning("Partner’s 401(k) may fall short of covering 85% of retirement needs.")

    # -------- Save Tab --------
    with tab6:
        st.subheader("⬇️ Save Your Simulation")
        profile = st.session_state.get("profile", {})
        insurance_type = st.session_state.get("insurance_type", "None")
        download_data = {
            "profile": profile,
            "insurance_type": insurance_type,
            "recommendations": st.session_state.get("recs", []),
            "insurance_recommendation": st.session_state.get("insurance_rec", {}),
            "risk_trajectory": st.session_state.get("risk_trajectory", []),
            "family_risk_summary": st.session_state.get("family_risk_summary", {}),
            "high_risk_score": st.session_state.get("high_risk_score", 0),
            "original_cost_df": st.session_state.get("cost_df", pd.DataFrame()).to_dict(orient="list") if st.session_state.get("cost_df") is not None else {},
            "updated_cost_df": st.session_state.get("updated_cost_df", pd.DataFrame()).to_dict(orient="list") if st.session_state.get("updated_cost_df") is not None else {}
        }
        download_json = json.dumps(download_data, indent=2)
        st.download_button(
            label="📥 Download Recommendation Report",
            data=download_json,
            file_name="health_strategy_recommendation.json",
            mime="application/json"
        )
