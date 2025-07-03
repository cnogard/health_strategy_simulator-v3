import streamlit as st
import matplotlib.pyplot as plt
from insurance_module import get_insurance_costs_over_time, get_base_premium, get_oop_correction_ratio
from simulator_core import generate_costs
from cost_library import estimate_uninsured_oop_by_year


def run_step_1(tab1):
    with tab1:
        st.header("Step 1: Profile & Insurance")
        age = st.number_input("Age", 18, 85, 30)
        user_age = age  # Preserve original user age
        gender = st.selectbox("Gender", ["male", "female"])
        health_status = st.selectbox("Health Status", ["healthy", "chronic", "high_risk"])
        # (continue with rest of logic...)

        # --- Chronic Condition Count (User) ---
        user_chronic_count = "None"
        if health_status == "chronic":
            st.markdown("### 🩺 Chronic Condition Count (User)")
            user_chronic_count = st.selectbox(
                "How many chronic conditions do you currently manage?",
                ["One", "Two or More"],
                key="user_chronic_count"
            )
        # --- Family Medical History (For Risk Assessment)
        st.markdown("### 🧬 Family Medical History (For Risk Assessment)")

        family_history_user = st.multiselect(
            "Your Family History:",
            ["Heart Disease", "Cancer", "Diabetes", "Neurological Disorders"],
            default=[]
        )
        family_status = st.selectbox("Family Status", ["single", "family"])
        family_history_partner = []
        st.session_state["family_history_user"] = family_history_user
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
        # --- Partner Family History (move after partner_age and partner_health_status) ---
        if family_status == "family":
            family_history_partner = st.multiselect(
                "Partner's Family History:",
                ["Heart Disease", "Cancer", "Diabetes", "Neurological Disorders"],
                default=[]
            )
        st.session_state["family_history_partner"] = family_history_partner

        # --- Chronic Condition Count (Partner) ---
        partner_chronic_count = "None"
        if family_status == "family":
            if partner_health_status == "chronic":
                st.markdown("### 🩺 Chronic Condition Count (Partner)")
                partner_chronic_count = st.selectbox(
                    "How many chronic conditions does your partner manage?",
                    ["One", "Two or More"],
                    key="partner_chronic_count"
                )


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
            # Only use premium_list if insurance_type is Employer-based
            premium_list = []
            if insurance_type == "Employer-based":
                premium_list = insurance_costs["premium"]
            # --- Use risk-adjusted OOP for year 1 ---
            # insurance_type_key assignment will be updated below for None
            if insurance_type == "Marketplace / Self-insured":
                insurance_type_key = "ACA"
            elif insurance_type == "Employer-based":
                insurance_type_key = "ESI"
            else:
                insurance_type_key = "Uninsured"
            # --- Patch: Use explicit OOP ratios for each insurance type ---
            def get_base_oop_ratio(insurance_type_key):
                if insurance_type_key == "ESI":
                    return 0.20  # 20% of full cost for ESI
                elif insurance_type_key == "ACA":
                    return 0.30  # 30% of full cost for ACA
                elif insurance_type_key == "Uninsured":
                    return 0.80  # 80% of full cost for uninsured
                else:
                    return 0.25  # fallback
            # Assume a typical "full cost" baseline for OOP, e.g., $10,000 per year, adjusted by health status
            base_full_costs = {
                'healthy': 5000,
                'chronic': 10000,
                'high_risk': 15000
            }
            base_full_cost = base_full_costs.get(health_status, 8000)
            base_oop_ratio = get_base_oop_ratio(insurance_type_key)
            base_oop = base_full_cost * base_oop_ratio
            oop_correction = get_oop_correction_ratio(user_age, insurance_type_key, health_status)
            risk_adjusted_oop = base_oop * oop_correction
            # --- Begin explicit insurance type handling for premium ---
            employee_premium = 0
            employer_premium = 0
            # (Removed redundant employee_premium assignment for Employer-based here)
            if insurance_type == "Marketplace / Self-insured":
                # Only define base_premium and estimated_employee_premium here
                base_premium = get_base_premium("ACA", "family")
                risk_multiplier = get_oop_correction_ratio(user_age, "ACA", health_status)
                estimated_employee_premium = base_premium * risk_multiplier
                employee_premium = estimated_employee_premium

            if insurance_type == "None":
                # Do not use premium_list for uninsured
                employee_premium = 0
                employer_premium = 0
            employer_premium = 0  # Explicitly ignore employer's contribution
            annual_oop = risk_adjusted_oop
        else:
            employee_premium = st.number_input("Employee Contribution ($/yr)", min_value=0, value=2000)
            employer_premium = st.number_input("Employer Contribution ($/yr)", min_value=0, value=6000 if insurance_type == "Employer-based" else 0)
            annual_oop = st.number_input("Estimated Annual OOP ($/yr)", min_value=0, value=4800)

        # Premium inflation rate (moved from Step 2)
        st.subheader("📈 Inflation Assumption")
        col_tuku, col_text = st.columns([1, 12])
        with col_tuku:
            st.image("Tuku_Analyst.png", width=60)
        with col_text:
            st.markdown("**Heads up! Inflation affects your projected insurance and out-of-pocket costs.** Don’t skip this step.")

        inflation_choice = st.radio("Use national average inflation or enter your own?", ["Use National Average", "I'll Choose"], key="inflation_rate_choice")

        if inflation_choice == "Use National Average":
            premium_inflation = 0.05  # 5% default national assumption
            st.markdown("📊 Using national inflation rate: **5% annually** (source: BLS Consumer Price Index)")
        else:
            user_input_inflation = st.slider("Set Your Annual Healthcare Inflation Rate (%)", 0, 10, 5)
            premium_inflation = user_input_inflation / 100

        st.session_state["expense_inflation"] = premium_inflation

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
                "partner_health_status": partner_health_status,
                "family_history_user": family_history_user,
                "family_history_partner": family_history_partner,
            }
            st.session_state["age"] = user_age
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
            if insurance_type == "None":
                insurance_type_key = "Uninsured"
            if insurance_type == "Marketplace / Self-insured":
                insurance_type_key = "ACA"
            if insurance_type == "Employer-based":
                insurance_type_key = "ESI"
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
                # Only use premium_list for Employer-based
                if insurance_type_key == "ESI":
                    if ('insurance_costs' not in locals() or len(premium_list) < n_years):
                        insurance_costs = get_insurance_costs_over_time(profile, n_years)
                        premium_list = insurance_costs["premium"]
                    premiums = extend_to_length(premium_list, n_years)
                elif insurance_type_key == "ACA":
                    # For Marketplace, recalculate premium projection
                    base_premium = get_base_premium("ACA", "family")
                    premiums = [base_premium * get_oop_correction_ratio(profile["age"] + i, "ACA", health_status) for i in range(n_years)]
                else:
                    premiums = [0] * n_years
                employer_premiums = [0] * n_years

                # --- Begin risk-adjusted OOP logic ---
                if insurance_type_key == "Uninsured":
                    base_full_costs = {
                        'healthy': 5000,
                        'chronic': 10000,
                        'high_risk': 15000
                    }
                    base_full_cost = base_full_costs.get(health_status, 8000)
                    total_oop_over_time = [
                        estimate_uninsured_oop_by_year(health_status, year + 1, base_full_cost)
                        for year in range(n_years)
                    ]
                else:
                    # Use explicit OOP ratios for ESI and ACA
                    def get_base_oop_ratio(insurance_type_key):
                        if insurance_type_key == "ESI":
                            return 0.20  # 20% of full cost for ESI
                        elif insurance_type_key == "ACA":
                            return 0.30  # 30% of full cost for ACA
                        elif insurance_type_key == "Uninsured":
                            return 0.80  # 80% of full cost for uninsured
                        else:
                            return 0.25  # fallback
                    base_full_costs = {
                        'healthy': 5000,
                        'chronic': 10000,
                        'high_risk': 15000
                    }
                    total_oop_over_time = []
                    for year in range(n_years):
                        age_this_year = profile["age"] + year
                        base_full_cost = base_full_costs.get(health_status, 8000)
                        base_oop_ratio = get_base_oop_ratio(insurance_type_key)
                        base_oop = base_full_cost * base_oop_ratio
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
            # Store monthly equivalents for later use (Step 6, etc.)
            st.session_state["monthly_premium"] = round(st.session_state.employee_premium / 12)
            st.session_state["monthly_oop"] = round(cost_df["OOP Cost"].iloc[first_year] / 12)
            # Reinforce zero premiums for uninsured in session state
            if insurance_type_key == "Uninsured":
                st.session_state.employee_premium = 0
                st.session_state["monthly_premium"] = 0
            # st.write(cost_df[["Age", "Healthcare Cost", "OOP Cost", "Premiums"]])  # Removed debug output
            st.line_chart(cost_df.set_index("Age")["Healthcare Cost"])
            st.success("Step 1 complete.")

