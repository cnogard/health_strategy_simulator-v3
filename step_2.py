import streamlit as st



def run_step_2(tab3):
    income_proj = st.session_state.get("income_proj", [])
    savings_proj = st.session_state.get("savings_proj", [])
    proj_401k = st.session_state.get("proj_401k", [])
    household_proj = st.session_state.get("household_proj", [])
    premiums = st.session_state.get("premiums", [])
    oop = st.session_state.get("oop", [])
    debt_proj = st.session_state.get("debt_proj", [])
    with tab3:
        # --- Ensure family_status is initialized in session_state to avoid AttributeError ---
        if "family_status" not in st.session_state:
            st.session_state.family_status = "single"
        # --- Ensure monthly_debt_input is initialized before use ---
        monthly_debt_input = st.session_state.get("debt_monthly_payment")
        if monthly_debt_input is None:
            debt_proj_list = st.session_state.get("debt_proj", [0])
            monthly_debt_input = debt_proj_list[0] if isinstance(debt_proj_list, list) and debt_proj_list else 0
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

            st.markdown("### 💵 Income & Tax Estimation")

            # --- User's income block, styled like partner's block ---
            net_user_income = st.number_input("User's Monthly Gross Income ($)", min_value=0, value=5000)
            est_tax_rate = st.number_input("User's Tax Rate (%)", min_value=0.0, max_value=100.0, value=25.0)
            income_growth = st.number_input("User's Expected Income Growth Rate (%)", min_value=0.0, max_value=20.0,
                                            value=2.0)
            # Fallback values to avoid UnboundLocalError for single users
            partner_net_income = 0
            net_income_monthly_partner = 0
            net_income_annual_partner = 0
            income_growth_partner = 0

            # --- Partner income/tax/growth fields (if family) ---
            if family_status == "family":
                partner_gross_income = st.number_input("Partner's Monthly Gross Income ($)", min_value=0, value=8000)
                partner_tax_rate = st.number_input("Partner's Tax Rate (%)", min_value=0.0, max_value=100.0, value=25.0)
                partner_income_growth = st.number_input("Partner's Expected Income Growth Rate (%)", min_value=0.0,
                                                        max_value=20.0, value=3.0)

            est_tax_rate_val = est_tax_rate / 100 if est_tax_rate > 1 else est_tax_rate


            if family_status == "family":
                partner_401k_contrib = st.session_state.get("partner_401k_contrib", 0)
                partner_401k_contribution = partner_401k_contrib
                monthly_401k_partner = partner_401k_contribution / 12 if partner_401k_contribution > 0 else 0
                partner_tax_rate_val = partner_tax_rate / 100 if partner_tax_rate > 1 else partner_tax_rate
                partner_gross_income_val = partner_gross_income if "partner_gross_income" in locals() else 0
                partner_income_growth_val = partner_income_growth / 100 if "partner_income_growth" in locals() else 0.03

                partner_net_income = (partner_gross_income_val - monthly_401k_partner) * (1 - partner_tax_rate_val)
                net_income_monthly_partner = partner_net_income
                net_income_annual_partner = partner_net_income * 12
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

            monthly_expenses = sum([
                housing_exp, transport_exp, food_exp,
                insurance_exp, entertainment_exp,
                childcare_exp, other_exp
            ])

            years = len(cost_df)
            # Save to session state if needed
            st.session_state["monthly_expenses"] = monthly_expenses
            # Save monthly expenses for available cash calculation in Step 2
            st.session_state["monthly_expenses_for_cash"] = monthly_expenses
            # Preserve user-entered value for available cash
            st.session_state["monthly_expenses_input"] = monthly_expenses  # Preserve user-entered value for available cash
            if monthly_expenses is not None:
                monthly_household = monthly_expenses  # Use actual input for year 1
                household_proj = [monthly_expenses * ((1 + inflation_rate) ** i) * 12 for i in range(years)]  # For future years


            st.markdown(f"#### 💰 Total Monthly Household Expenses: ${monthly_expenses:,.0f}")


            # --- 💳 Debt Payments ---
            st.markdown("### 💳 Monthly Debt Payments")
            monthly_debt_input = st.number_input("Monthly Debt Payments (Credit Cards, Loans)", min_value=0, value=1500)

            # --- Inflation rate pulled from Step 1 ---
            inflation = st.session_state.get("inflation_rate", 0.03)

            # --- Retrieve projection length ---
            st.session_state["years"] = years

            # --- Use saved monthly expenses for future projection calculations
            monthly_expenses = st.session_state.get("monthly_expenses_for_cash", 0)
            # --- Project household expenses and debt over time ---
            household_expenses_annual = st.session_state.get("monthly_expenses_input", 0) * 12
            household_proj = [household_expenses_annual * ((1 + inflation_rate) ** i) for i in range(years)]
            # Project debt over time based on user input monthly_debt_input
            debt_proj = [monthly_debt_input * ((1 + inflation_rate) ** i) for i in range(years)]

            # --- Projected Health Premiums ---
            base_premium = st.session_state.get("base_premium", 6000)
            premiums = [base_premium * ((1 + inflation) ** i) for i in range(years)]
            st.session_state["premiums"] = premiums
            st.session_state["projected_premiums"] = premiums
            st.session_state["debt_proj"] = debt_proj

            # --- Store in session state for downstream use ---
            st.session_state.household_proj = household_proj

            # --- 🧓 Long-Term Care Projection ---
            ltc_enabled = st.session_state.get("ltc_enabled", False)
            ltc_annual_cost = st.session_state.get("ltc_annual_cost", 0)
            user_age = profile.get("age", 30)

            if ltc_enabled:
                ltc_proj = [
                    ltc_annual_cost * ((1 + inflation_rate) ** i) if (user_age + i) >= 75 else 0
                    for i in range(years)
                ]
            else:
                ltc_proj = [0] * years

            st.session_state["ltc_proj"] = ltc_proj



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
                partner_401k_contrib = 0
                partner_employer_401k_contrib = 0



            # --- Net user income after 401(k) and tax ---
            monthly_401k_user = contrib_401k_employee / 12
            est_tax_rate_val = est_tax_rate / 100 if est_tax_rate > 1 else est_tax_rate
            net_user_income = (net_user_income - monthly_401k_user) * (1 - est_tax_rate_val)
            user_income = net_user_income * 12  # annualized

            if family_status == "family":
                # --- Partner Net Income After 401(k) and Tax (Final Patch) ---
                monthly_401k_partner = partner_401k_contrib / 12
                partner_tax_rate_val = partner_tax_rate / 100 if partner_tax_rate > 1 else partner_tax_rate
                partner_net_income = (partner_gross_income - monthly_401k_partner) * (1 - partner_tax_rate_val)
                net_income_monthly_partner = partner_net_income
                net_income_annual_partner = partner_net_income * 12

            # --- NEW: Net income after 401(k) logic (using corrected formula) ---
            if family_status == "family":
                st.write("DEBUG: Net Income After 401(k) (Partner):", net_income_monthly_partner)
            total_net_income = net_user_income + partner_net_income
            net_income_monthly = total_net_income
            st.session_state.net_income_monthly = net_income_monthly
            st.session_state.net_income_monthly_partner = net_income_monthly_partner
            net_income_annual = total_net_income * 12

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
                    net_user_income * 12 * ((1 + income_growth) ** i) if (
                        user_age + i) < retirement_age else net_user_income * 12 * 0.4
                    for i in range(years)
                ]

                # --- Partner income projection using new variables ---
                if family_status == "family":
                    income_proj_partner = []
                    for i in range(years):
                        partner_age_i = partner_age + i  # partner's age this year
                        if partner_age_i < 65:
                            income = net_income_monthly_partner * 12 * ((1 + income_growth_partner) ** i)
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

                st.session_state.net_user_income = net_user_income
                st.session_state.net_income_annual = net_income_annual
                st.session_state.income_growth = income_growth
                st.session_state.monthly_expenses = monthly_expenses
                st.session_state.debt_monthly_payment = monthly_debt_input
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
            # Always use premium_cost and oop_cost from session_state (set in Step 1)
            premium_cost = st.session_state.get("premium_cost", 0)
            oop_cost = st.session_state.get("oop_cost", 0)
            monthly_premium = premium_cost / 12
            monthly_oop = oop_cost / 12

            household_expenses = st.session_state.get("monthly_expenses", 0)
            monthly_household = household_expenses
            monthly_savings = annual_contrib / 12

            # Use final monthly net income values from above (already net and monthly)
            net_income_user_final = st.session_state.get("net_user_income", 0)
            net_income_partner_final = st.session_state.get("net_income_monthly_partner", 0)
            total_net_income = net_income_user_final + net_income_partner_final

            # ✅ FIXED: Remove incorrect division by 12
            available_cash = total_net_income - monthly_premium - monthly_oop - household_expenses - monthly_debt_input - monthly_savings
            st.session_state["available_cash"] = available_cash


            # Display available cash using st.success with formatting and emoji
            # ✅ Only display estimated available cash after user submits Step 2
            if st.session_state.get("step2_submitted"):
                available_cash = st.session_state.get("available_cash", 0)
                st.markdown(f"💰 Estimated Available Cash (Post Premium + OOP): ${available_cash:,.0f}/month")
                if available_cash < 0:
                    st.error(
                        "⚠️ You do not have enough available cash to meet your current expenses. Please review your income, expenses, or savings strategy.")

            # Optional clean Step 2 submit button to force user to confirm inputs
            if st.button("Submit Step 2"):
                st.session_state["step2_submitted"] = True
                st.session_state["step3_submitted"] = False
                st.session_state["current_step"] = 3  # optional progression
                st.success("✅ Step 2 completed. Proceed to Step 3.")
                # Show available cash summary after submission
                if "available_cash" in st.session_state:
                    available_cash = st.session_state["available_cash"]
                    st.markdown(f"💰 Estimated Available Cash (Post Premium + OOP): ${available_cash:,.0f}/month")
                    if available_cash < 0:
                        st.error("⚠️ You do not have enough available cash to meet your current expenses. Please review your income, expenses, or savings strategy.")



        # (Moved display logic for available cash into the button block above.)