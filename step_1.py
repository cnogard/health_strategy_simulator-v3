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
        # --- Deductible Choice for ESI and ACA ---
        deductible_choice = None
        if insurance_type in ["Employer-based", "Marketplace / Self-insured"]:
            deductible_choice = st.selectbox(
                "What is your annual deductible amount?",
                options=["$0", "$500", "$1,500"],
                help="This affects your premium and OOP range. Higher deductibles lower premiums but increase upfront costs."
            )
            st.session_state["deductible_level"] = deductible_choice

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
            # Map UI to internal insurance type
            if insurance_type == "Employer-based":
                insurance_type_key = "ESI"
            elif insurance_type == "Marketplace / Self-insured":
                insurance_type_key = "ACA"
            else:
                insurance_type_key = "Uninsured"

            # --- New Deductible-based logic for ESI and ACA ---
            if insurance_type_key in ["ESI", "ACA"]:
                # Use the deductible_choice
                selected_deductible = st.session_state.get("deductible_level", "$500")
                # Use new logic as per instructions
                if selected_deductible == "$0":
                    annual_premium = 1847 if insurance_type_key == "ESI" else 6800
                    oop_estimate = 1000
                elif selected_deductible == "$500":
                    annual_premium = 1600 if insurance_type_key == "ESI" else 5950
                    oop_estimate = 1800
                else:  # "$1,500"
                    annual_premium = 1327 if insurance_type_key == "ESI" else 5100
                    oop_estimate = 2200
                employee_premium = annual_premium
                employer_premium = 0
                annual_oop = oop_estimate
                # Save to session_state for downstream use
                st.session_state["deductible_level"] = selected_deductible
                st.session_state["premium"] = annual_premium
                st.session_state["oop_cost"] = oop_estimate
                # Save year 1 values for downstream use and apply across all years
                st.session_state["premium_year1"] = annual_premium
                st.session_state["oop_year1"] = oop_estimate
            elif insurance_type_key == "Uninsured":
                employee_premium = 0
                employer_premium = 0
                # Use uninsured OOP logic below
                # annual_oop assigned below
            else:
                employee_premium = 0
                employer_premium = 0
                annual_oop = 0
            # For uninsured, use the original logic for OOP
            if insurance_type_key == "Uninsured":
                if health_status == "healthy":
                    annual_oop_uninsured = 75000 / 60
                elif health_status == "chronic":
                    annual_oop_uninsured = 459000 / 60
                else:  # high-risk
                    annual_oop_uninsured = 472000 / 60
                annual_oop = annual_oop_uninsured
                # Save year 1 values for downstream use and apply across all years
                st.session_state["premium_year1"] = 0
                st.session_state["oop_year1"] = annual_oop_uninsured
            # Store monthly OOP and premium in session state for consistency
            st.session_state["monthly_oop"] = annual_oop / 12
            st.session_state["monthly_premium"] = round(employee_premium / 12)
            st.session_state["employee_premium"] = employee_premium
            st.session_state["employer_premium"] = employer_premium
            st.session_state["premium"] = employee_premium
            st.session_state["oop_cost"] = annual_oop
            # The rest of the logic below will use these session_state values for projections and reporting
        else:
            employee_premium = st.number_input("Employee Contribution ($/yr)", min_value=0, value=2000)
            employer_premium = st.number_input("Employer Contribution ($/yr)", min_value=0, value=6000 if insurance_type == "Employer-based" else 0)
            annual_oop = st.number_input("Estimated Annual OOP ($/yr)", min_value=0, value=4800)
            # Store monthly OOP and premium in session state for consistency
            st.session_state["monthly_oop"] = annual_oop / 12
            st.session_state["monthly_premium"] = round(employee_premium / 12)
            st.session_state["employee_premium"] = employee_premium
            st.session_state["employer_premium"] = employer_premium
            st.session_state["premium"] = employee_premium
            st.session_state["oop_cost"] = annual_oop
        # --- Uninsured lifetime-averaged OOP logic for monthly_oop ---
        # (Moved to logic above for unified assignment and session_state saving)

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
            base_employee_premium = st.session_state.get("employee_premium", 0)
            base_employer_premium = st.session_state.get("employer_premium", 0)
            # --- Use insurance_module's premium_list/oop_list if available and user chose averages ---
            use_avg_inputs_bool = (use_avg_inputs == "Yes")
            # If using national averages, use deductible-based values for projections if ESI/ACA, otherwise previous logic
            if use_avg_inputs_bool:
                def extend_to_length(lst, n):
                    if len(lst) >= n:
                        return lst[:n]
                    elif len(lst) == 0:
                        return [0] * n
                    else:
                        return lst + [lst[-1]] * (n - len(lst))
                # For ESI/ACA, use deductible-based premium and OOP for all years
                if insurance_type_key in ["ESI", "ACA"]:
                    premiums = [st.session_state.get("premium", 0)] * n_years
                    employer_premiums = [0] * n_years
                    total_oop_over_time = [st.session_state.get("oop_cost", 0)] * n_years
                elif insurance_type_key == "Uninsured":
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
                    premiums = [0] * n_years
                    employer_premiums = [0] * n_years
                else:
                    # fallback
                    premiums = [0] * n_years
                    employer_premiums = [0] * n_years
                    total_oop_over_time = [0] * n_years
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
            # Always store monthly_oop as calculated above (already set for all cases)
            # Reinforce zero premiums for uninsured in session state
            if insurance_type_key == "Uninsured":
                st.session_state.employee_premium = 0
                st.session_state["monthly_premium"] = 0
            # st.write(cost_df[["Age", "Healthcare Cost", "OOP Cost", "Premiums"]])  # Removed debug output
            st.line_chart(cost_df.set_index("Age")["Healthcare Cost"])
            st.success("Step 1 complete.")

