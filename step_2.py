import streamlit as st



def run_step_2(tab3):
    with tab3:
       # --- Use premium inflation from Step 1 as selected by the user ---
        inflation_rate = st.session_state.get("premium_inflation", 0.05)
        # --- Ensure profile and key variables are always defined to avoid reference errors ---
        profile = st.session_state.get("profile", {})
        family_status = profile.get("family_status", "single")
        partner_age = profile.get("partner_age", 65)
        age = profile.get("age", 30)
        health_status = profile.get("health_status", "healthy")
        insurance_type = profile.get("insurance_type", "None")
        partner_401k_contrib = st.session_state.get("partner_401k_contrib", 0)
        partner_employer_401k_contrib = st.session_state.get("partner_employer_401k_contrib", 0)
        st.header("Step 2: Financial Inputs")

        # -------- Step 2: Financial Inputs --------
        # Inflation Assumptions section removed (if present)
        if "cost_df" in st.session_state and not st.session_state.get("step2_submitted"):
            cost_df = st.session_state.cost_df
            # insurance_type and profile are already defined above
            oop_first_year = round(cost_df["OOP Cost"].iloc[0], 2)
            premium_first_year = round(cost_df["Premiums"].iloc[0], 2)
            net_income_monthly = 0

            st.markdown("### 💵 Income & Tax Estimation")
            monthly_income = st.number_input("Monthly Gross Income ($)", 0, value=5000)
            est_tax_rate = st.slider("Estimated Tax Rate (%)", 0.0, 50.0, 25.0) / 100
            # --- Income growth slider moved ABOVE partner income block ---
            income_growth = st.slider("Income Growth (%)", 0.0, 10.0, 2.0) / 100
            # --- Partner income/inputs for family, after user income ---
            if family_status == "family":
                monthly_income_partner = st.number_input("Partner Monthly Gross Income ($)", min_value=0,
                                                         value=4000, key="monthly_income_partner")
                est_tax_rate_partner = st.slider("Estimated Tax Rate for Partner (%)", 0, 50, 20,
                                                 key="tax_rate_partner") / 100
                net_income_monthly_partner = monthly_income_partner * (1 - est_tax_rate_partner)
            else:
                net_income_monthly_partner = 0
            net_income_monthly_user = monthly_income * (1 - est_tax_rate)
            net_income_monthly = net_income_monthly_user + net_income_monthly_partner
            st.session_state.net_income_monthly = net_income_monthly
            st.session_state.net_income_monthly_partner = net_income_monthly_partner
            net_income_annual = net_income_monthly * 12


            # --- Fallbacks for partner income/inputs ---
            net_income_annual_partner = 0
            income_growth_partner = 0
            # --- Partner income/inputs for family ---
            if family_status == "family":
                net_income_annual_partner = net_income_monthly_partner * 12
                income_growth_partner = st.slider("Partner's Income Growth Rate (%)", 0.0, 10.0, 3.0) / 100

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
                    # Use only income_growth in income projection (remove inflation_rate)
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
                        # Use partner's savings if modeled separately; for now, use same as user
                        # If you want partner's savings to be separate, add inputs and logic here.
                        # For now, only project partner 401k.
                        partner_age_val = profile.get("partner_age", 65)
                        # partner_401k_contrib and partner_employer_401k_contrib already defined at top-level
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

                    # Calculate available cash: net_income_monthly (user+partner) - premiums - oop - household_expenses - debt_payments - monthly_savings_contrib
                    # Corrected logic for premium and OOP handling
                    # OOP is already set as: oop_first_year = round(cost_df["OOP Cost"].iloc[0], 2)
                    if insurance_type == "None":
                        premium_cost = 0
                    elif insurance_type == "Employer":
                        premium_cost = employee_premium
                    else:  # Marketplace / Self-insured
                        premium_cost = premium_first_year

                    available_cash = net_income_monthly - (premium_cost / 12) - (oop_first_year / 12) - monthly_expenses - debt_monthly_payment - monthly_savings_contrib
                    st.session_state.available_cash = max(0, available_cash)

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