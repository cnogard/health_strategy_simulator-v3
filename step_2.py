import streamlit as st



def run_step_2(tab3):
    with tab3:
       # --- Use premium inflation from Step 1 as selected by the user ---
        inflation_rate = st.session_state.get("premium_inflation", 0.05)
        # --- Ensure profile and key variables are always defined to avoid reference errors ---
        profile = st.session_state.get("profile", {})
        family_status = profile.get("family_status", "single")
        partner_age = profile.get("partner_age", 65)
        insurance_type = profile.get("insurance_type", "None")
        partner_401k_contrib = st.session_state.get("partner_401k_contrib", 0)
        partner_employer_401k_contrib = st.session_state.get("partner_employer_401k_contrib", 0)
        st.header("Step 2: Financial Inputs")

        # -------- Step 2: Financial Inputs --------
        # Inflation Assumptions section removed (if present)
        if "cost_df" in st.session_state and not st.session_state.get("step2_submitted"):
            cost_df = st.session_state.cost_df
            # insurance_type and profile are already defined above
            if not cost_df.empty and "OOP Cost" in cost_df.columns:
                oop_first_year = round(cost_df["OOP Cost"].iloc[0], 2)
            else:
                oop_first_year = 0  # Fallback if data is missing
                st.warning("Unable to calculate OOP for the first year. Please check Step 1 inputs.")
            if not cost_df.empty and "Premiums" in cost_df.columns:
                premium_first_year = round(cost_df["Premiums"].iloc[0], 2)
            else:
                premium_first_year = 0  # Fallback if data is missing

            st.markdown("### 💵 Income & Tax Estimation")
            monthly_income = st.number_input("Monthly Gross Income ($)", 0, value=5000)
            est_tax_rate = st.slider("Estimated Tax Rate (%)", 0.0, 50.0, 25.0) / 100
            # --- Income growth slider moved ABOVE partner income block ---
            income_growth = st.slider("Income Growth (%)", 0.0, 10.0, 2.0) / 100

            # --- Partner income/tax/growth fields (re-inserted) ---
            if family_status == "family":
                partner_gross_income = st.number_input("Partner's Monthly Gross Income ($)", min_value=0, value=8000)
                partner_tax_rate = st.number_input("Partner's Tax Rate (%)", min_value=0.0, max_value=100.0, value=25.0)
                partner_income_growth = st.number_input("Partner's Expected Income Growth Rate (%)", min_value=0.0, max_value=20.0, value=3.0)

            # --- 401(k)-adjusted net income calculation (401k subtracted before tax) ---
            tax_rate = est_tax_rate
            user_income = monthly_income * 12
            contrib_401k_employee = 0  # Ensure variable is always defined before use, will be overwritten below
            # contrib_401k_employee will be set below after input

            # We'll calculate net_income_user after contrib_401k_employee is input, see below.
            net_income_partner = 0
            partner_income = 0
            contrib_401k_partner = 0
            net_income_monthly_partner = 0

            # We'll calculate these after 401k inputs below.


            # --- Fallbacks for partner income/inputs ---
            net_income_annual_partner = 0
            income_growth_partner = 0
            # --- Partner income/inputs for family ---
            if family_status == "family":
                # Use the new partner fields if present, else fallback
                partner_gross_income_val = partner_gross_income if "partner_gross_income" in locals() else 0
                partner_tax_rate_val = partner_tax_rate / 100 if "partner_tax_rate" in locals() else tax_rate
                partner_income_growth_val = partner_income_growth / 100 if "partner_income_growth" in locals() else 0.03
                net_income_monthly_partner = (partner_gross_income_val - (partner_401k_contrib / 12)) * (1 - partner_tax_rate_val)
                net_income_annual_partner = net_income_monthly_partner * 12
                income_growth_partner = partner_income_growth_val

            # --- 🛒 Household Expenses ---
            st.markdown("### 🛒 Household Expenses")

            # Always show itemized expense inputs with BLS 2023 defaults
            st.markdown("#### 📋 Monthly Household Expenses (BLS 2023 Defaults Provided)")
            housing_exp = st.number_input("Monthly Housing ($)", min_value=0, value=2000)
            transport_exp = st.number_input("Monthly Transportation ($)", min_value=0, value=800)
            food_exp = st.number_input("Monthly Food ($)", min_value=0, value=1000)
            insurance_exp = st.number_input("Monthly Insurance & Pensions ($)", min_value=0, value=1200)
            entertainment_exp = st.number_input("Monthly Entertainment ($)", min_value=0, value=500)
            childcare_exp = st.number_input("Monthly Childcare / School ($)", min_value=0, value=500)
            other_exp = st.number_input("Other Monthly Expenses ($)", min_value=0, value=440)

            itemized_total = sum([
                housing_exp, transport_exp, food_exp,
                insurance_exp, entertainment_exp,
                childcare_exp, other_exp
            ])
            st.write("Itemized Total Household Expenses:", itemized_total)
            st.markdown(f"#### 💰 Total Monthly Household Expenses: ${itemized_total:,.0f}")
            st.markdown(f"**Total Monthly Household Expenses:** ${itemized_total:,}")
            monthly_expenses = itemized_total
            # Save to session state if needed
            st.session_state["monthly_expenses"] = monthly_expenses
            st.session_state["itemized_total"] = itemized_total

            # --- 💳 Debt Payments ---
            st.markdown("### 💳 Monthly Debt Payments")
            debt_monthly_payment = st.number_input("Monthly Debt Payments (Credit Cards, Loans)", min_value=0,
                                                   value=1500)

            # --- Inflation rate pulled from Step 1 ---
            inflation = st.session_state.get("inflation_rate", 0.03)

            # --- Retrieve projection length ---
            years = len(cost_df)
            st.session_state["years"] = years

            # --- Project household expenses and debt over time ---
            household_proj = [monthly_expenses * 12 * ((1 + inflation) ** i) for i in range(years)]
            debt_proj = [debt_monthly_payment * 12 for _ in range(years)]  # constant assumption

            # --- Projected Health Premiums ---
            base_premium = st.session_state.get("base_premium", 6000)
            premiums = [base_premium * ((1 + inflation) ** i) for i in range(years)]
            st.session_state["premiums"] = premiums
            st.session_state["projected_premiums"] = premiums

            # --- Store in session state for downstream use ---
            st.session_state.household_proj = household_proj
            st.session_state.debt_proj = debt_proj

            # --- 💼 401(k) Contributions ---
            st.markdown("### 💼 401(k) Contributions")
            start_401k_user = st.number_input("Your Starting 401(k) Balance ($)", min_value=0, value=0)
            profile["start_401k_user"] = start_401k_user
            st.session_state.profile = profile
            contrib_401k_employee = st.number_input(
                "Annual Employee 401(k) Contribution ($)",
                min_value=0,
                value=0
            )
            contrib_401k_employer = st.number_input(
                "Annual Employer 401(k) Match ($)",
                min_value=0,
                value=0
            )
            growth_401k = st.slider("401(k) Growth Rate (%)", 0.0, 10.0, 5.0) / 100
            # --- Partner 401(k) Contributions: Annual only ---
            if family_status == "family":
                st.subheader("💼 Partner 401(k) Contributions")
                start_401k_partner = st.number_input("Partner's Starting 401(k) Balance ($)", min_value=0,
                                                     value=0)
                profile["start_401k_partner"] = start_401k_partner
                st.session_state.profile = profile
                partner_401k_contrib = st.number_input(
                    "Partner's Annual 401(k) Contribution ($)",
                    min_value=0,
                    value=0,
                    key="partner_401k_contrib"
                )
                partner_employer_401k_contrib = st.number_input(
                    "Partner's Annual Employer 401(k) Match ($)",
                    min_value=0,
                    value=0,
                    key="partner_employer_401k_contrib"
                )
                partner_growth_401k = st.slider("Partner's 401(k) Growth Rate (%)", 0.0, 10.0, 5.0) / 100
                profile["partner_growth_401k"] = partner_growth_401k
                st.session_state.profile = profile
            else:
                # Optional: clear any previous partner values if not family
                st.session_state.pop("partner_401k_contrib", None)
                st.session_state.pop("partner_employer_401k_contrib", None)

            # --- DEBUG: Show 401(k) contributions for user and partner ---
            user_401k_contribution = contrib_401k_employee
            st.write(f"DEBUG: 401(k) Contribution (User): {user_401k_contribution}")
            if family_status == "family":
                partner_401k_contribution = partner_401k_contrib
                st.write(f"DEBUG: 401(k) Contribution (Partner): {partner_401k_contribution}")

            # --- NEW: Net income after 401(k) logic ---
            monthly_401k_contribution = contrib_401k_employee / 12
            monthly_gross_income = user_income / 12
            income_minus_401k = monthly_gross_income - monthly_401k_contribution
            net_income_user = income_minus_401k * (1 - tax_rate)
            st.write("DEBUG: Net Income After 401(k) (User):", net_income_user)

            if family_status == "family":
                # Use the new partner fields for net income calculation
                st.write("DEBUG: Net Income After 401(k) (Partner):", net_income_monthly_partner)
                net_income_partner = net_income_monthly_partner
            else:
                net_income_partner = 0
                net_income_monthly_partner = 0
            net_income_monthly_user = net_income_user
            total_net_income = net_income_user + (net_income_partner if family_status == "family" else 0)
            st.write("DEBUG: Total Net Income:", total_net_income)
            net_income_monthly = total_net_income
            st.session_state.net_income_monthly = net_income_monthly
            st.session_state.net_income_monthly_partner = net_income_monthly_partner
            net_income_annual = net_income_monthly * 12

            # --- Pension Income UI Block ---
            from pension_utils import DEFAULT_PENSION_VALUES

            st.markdown("### 🧓 Pension Income")

            # --- User Pension Input ---
            has_pension_user = st.radio("Do you have a pension plan?", ["No", "Yes"], index=0)
            if has_pension_user == "Yes":
                knows_pension_user = st.radio("Do you know the expected annual pension amount?", ["No", "Yes"], index=1)
                if knows_pension_user == "Yes":
                    pension_user = st.number_input(
                        "Your Estimated Annual Pension at Retirement ($)",
                        min_value=0,
                        value=DEFAULT_PENSION_VALUES["private"]
                    )
                else:
                    pension_type_user = st.selectbox("What type of pension is it?", ["Private", "State", "Federal"])
                    pension_user = DEFAULT_PENSION_VALUES[pension_type_user.lower()]
            else:
                pension_user = 0

            # --- Partner Pension Input ---
            if family_status == "family":
                has_pension_partner = st.radio("Does your partner have a pension plan?", ["No", "Yes"], index=0, key="partner_pension_radio")
                if has_pension_partner == "Yes":
                    knows_pension_partner = st.radio("Do they know the expected annual pension amount?", ["No", "Yes"], index=1, key="knows_partner_pension")
                    if knows_pension_partner == "Yes":
                        pension_partner = st.number_input(
                            "Partner's Estimated Annual Pension at Retirement ($)",
                            min_value=0,
                            value=DEFAULT_PENSION_VALUES["private"],
                            key="partner_pension_amount"
                        )
                    else:
                        pension_type_partner = st.selectbox(
                            "Partner's Pension Type",
                            ["Private", "State", "Federal"],
                            key="partner_pension_type"
                        )
                        pension_partner = DEFAULT_PENSION_VALUES[pension_type_partner.lower()]
                else:
                    pension_partner = 0
            else:
                pension_partner = 0

            st.session_state["pension_user"] = pension_user
            st.session_state["pension_partner"] = pension_partner

            # --- 💰 Savings Profile ---
            st.markdown("### 💰 Savings Profile")
            savings_balance = st.number_input("How much have you saved?", min_value=0, step=100, value=20000)
            st.session_state["savings_balance"] = savings_balance
            # The following input is now optional/redundant, but kept for backward compatibility:
            # savings_start = st.number_input("Current Savings Balance ($)", 0, value=10000)
            savings_start = savings_balance
            savings_growth = st.slider("Expected Savings Growth (%)", 0.0, 10.0, 3.0) / 100
            annual_contrib = st.number_input("Annual Savings Contribution ($)", 0, value=1200)
            monthly_savings_contrib = annual_contrib / 12
            savings_goals = st.multiselect(
                "What is your savings primarily for?",
                ["Home", "Education", "Vacations", "Retirement", "Health", "Rainy Day"],
                default=["Retirement", "Health"]
            )

            if st.button("Run Step 2"):
                years = len(cost_df)
                user_age = profile.get("age", 30)
                retirement_age = 65
                # --- Revised Retirement-aware income projection (stop regular income after retirement) ---
                income_proj = [
                    net_income_annual * ((1 + income_growth) ** i) if (
                        user_age + i) < retirement_age else net_income_annual * 0.4
                    for i in range(years)
                ]

                # --- Partner income projection using new variables ---
                if family_status == "family":
                    income_proj_partner = []
                    for i in range(years):
                        partner_age_i = partner_age + i  # partner's age this year
                        if partner_age_i < 65:
                            income = net_income_annual_partner * ((1 + income_growth_partner) ** i)
                        else:
                            income = 0
                        income_proj_partner.append(income)
                else:
                    income_proj_partner = [0 for _ in range(years)]

                # --- Combined income projection ---
                if family_status == "family":
                    combined_income_proj = [user + partner for user, partner in
                                            zip(income_proj, income_proj_partner)]
                else:
                    combined_income_proj = income_proj

                # Store the combined projection in session state
                st.session_state.combined_income_proj = combined_income_proj

                # --- Revised savings and 401(k) projections: contributions before retirement, only growth after ---
                # User projections
                proj_401k = []
                savings_proj = []
                user_401k_balance = profile.get("start_401k_user", 0)
                current_401k = user_401k_balance
                current_savings = savings_start
                monthly_contrib_401k = (contrib_401k_employee + contrib_401k_employer) / 12
                monthly_savings = annual_contrib / 12
                growth_rate_401k = growth_401k
                growth_rate_savings = savings_growth
                for i in range(years):
                    age_iter = user_age + i
                    if age_iter < retirement_age:
                        current_401k = current_401k * (1 + growth_rate_401k + inflation_rate) + monthly_contrib_401k * 12
                        current_savings = current_savings * (1 + growth_rate_savings + inflation_rate) + monthly_savings * 12
                    else:
                        current_401k = current_401k * (1 + growth_rate_401k + inflation_rate)
                        current_savings = current_savings * (1 + growth_rate_savings + inflation_rate)
                    proj_401k.append(current_401k)
                    savings_proj.append(current_savings)

                # Partner projections for family mode
                if family_status == "family":
                    proj_401k_partner = []
                    savings_proj_partner = []
                    partner_401k_balance = profile.get("start_401k_partner", 0)
                    current_401k_partner = partner_401k_balance
                    partner_age_val = profile.get("partner_age", 65)
                    monthly_contrib_401k_partner = (partner_401k_contrib + partner_employer_401k_contrib) / 12
                    growth_401k_partner = profile.get("partner_growth_401k", growth_401k)
                    for i in range(years):
                        age_partner = partner_age_val + i
                        if age_partner < retirement_age:
                            current_401k_partner = current_401k_partner * (
                                1 + growth_401k_partner + inflation_rate) + monthly_contrib_401k_partner * 12
                        else:
                            current_401k_partner = current_401k_partner * (1 + growth_401k_partner + inflation_rate)
                        proj_401k_partner.append(current_401k_partner)
                else:
                    proj_401k_partner = [0] * years
                # --- Store 401k projections in session state unconditionally before marking submission ---
                st.session_state["proj_401k"] = proj_401k
                if family_status == "family":
                    st.session_state["proj_401k_partner"] = proj_401k_partner
                else:
                    st.session_state["proj_401k_partner"] = [0] * years

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

                # insurance_type already defined at top-level
                employee_premium = st.session_state.get("employee_premium", 0)

                monthly_expenses = st.session_state.get("monthly_expenses", 0)
                debt_monthly_payment = st.session_state.get("debt_monthly_payment", 0)

                # --- NEW: Joint income and expenses computation for available cash ---
                # Premium escalation logic (first year only for available cash debug)
                if insurance_type == "None":
                    premium_cost = 0
                elif insurance_type == "Employer":
                    premium_cost = employee_premium
                else:  # Marketplace / Self-insured
                    premium_cost = premium_first_year
                # OOP escalation (first year only)
                oop_cost = oop_first_year
                # Calculate monthly values for clarity (first year only)
                monthly_premium = premium_cost / 12
                monthly_oop = oop_cost / 12
                monthly_household = household_proj[0] / 12
                monthly_debt = debt_proj[0] / 12
                # Apply joint income if family (already calculated above with new logic)
                # total_net_income is already user_net_income + partner_net_income
                # Joint savings (user input is assumed joint regardless of family status)
                monthly_savings = annual_contrib / 12
                # Total monthly expenses
                total_expenses = monthly_premium + monthly_oop + monthly_household + monthly_debt + monthly_savings
                # Available cash after all expenses
                available_cash = total_net_income - total_expenses
                # Debug output for troubleshooting
                st.write("DEBUG: Family Status:", family_status)
                st.write("DEBUG: Net Income (User):", net_income_monthly_user)
                st.write("DEBUG: Net Income (Partner):", net_income_monthly_partner)
                st.write("DEBUG: Total Net Income:", total_net_income)
                st.write("DEBUG: Monthly Premium:", monthly_premium)
                st.write("DEBUG: Monthly OOP:", monthly_oop)
                st.write("DEBUG: Household Expenses:", monthly_household)
                st.write("DEBUG: Monthly Debt:", monthly_debt)
                st.write("DEBUG: Monthly Savings:", monthly_savings)
                st.write("DEBUG: Estimated Available Cash:", available_cash)

                # Calculate available cash projection year-over-year with premium and OOP escalation
                available_cash_projection = []
                for i in range(years):
                    # Premium escalation logic
                    if insurance_type == "None":
                        premium_cost = 0
                    elif insurance_type == "Employer":
                        premium_cost = employee_premium * ((1 + inflation_rate) ** i)
                    else:  # Marketplace / Self-insured
                        premium_cost = premium_first_year * ((1 + inflation_rate) ** i)
                    # OOP escalation
                    oop_cost = oop_first_year * ((1 + inflation_rate) ** i)
                    # Calculate monthly values for clarity
                    monthly_income_user = income_proj[i] / 12
                    monthly_income_partner = income_proj_partner[i] / 12 if family_status == "family" else 0
                    monthly_income = monthly_income_user + monthly_income_partner
                    monthly_premium = premium_cost / 12
                    monthly_oop = oop_cost / 12
                    monthly_household = household_proj[i] / 12
                    monthly_debt = debt_proj[i] / 12
                    monthly_savings = annual_contrib / 12

                    # Use the same joint income/expenses logic as above for projection
                    total_net_income_proj = monthly_income
                    total_expenses_proj = monthly_premium + monthly_oop + monthly_household + monthly_debt + monthly_savings
                    cash = total_net_income_proj - total_expenses_proj
                    available_cash_projection.append(max(0, cash))
                st.session_state["available_cash_projection"] = available_cash_projection
                # For backward compatibility, set available_cash as year 1 (first year) value
                st.session_state.available_cash = available_cash_projection[0]

                st.success(
                    f"💰 Estimated Available Cash (Post Premium + OOP): ${st.session_state.available_cash:,.0f}/month")

                # Set step2_submitted True and reset step3_submitted only after all calculations
                st.session_state.step2_submitted = True
                st.session_state.step3_submitted = False
                st.write("Debug: Step 2 completed.")

        if "available_cash" in st.session_state:
            rounded_cash = round(st.session_state.available_cash, 2)

            if rounded_cash <= 0:
                st.warning(
                    "⚠️ Your expenses may exceed your net income. Please review your household spending or debt to ensure you can fund healthcare and savings goals.")