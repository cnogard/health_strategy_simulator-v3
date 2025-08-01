def compute_retirement_drawdown(chart_ages, deficit_values, savings_proj, proj_401k_combined,
                                retirement_index, total_pension, estimated_ss):
    used_capital = []
    remaining_capital = []
    unfunded_gap = []
    pension_stream = []
    ss_stream = []

    savings_total = savings_proj[retirement_index] if 0 <= retirement_index < len(savings_proj) else 0
    proj_401k_val = proj_401k_combined[retirement_index] if 0 <= retirement_index < len(proj_401k_combined) else 0
    ss_per_year = estimated_ss / len(chart_ages) if chart_ages else 0
    current_capital = savings_total + proj_401k_val

    for i, age in enumerate(chart_ages):
        pension = total_pension
        ss = ss_per_year
        total_income = pension + ss

        deficit = deficit_values[i]
        uncovered = max(deficit - total_income, 0)

        used = min(uncovered, current_capital)
        gap = max(uncovered - used, 0)
        current_capital -= used

        used_capital.append(used)
        remaining_capital.append(max(current_capital, 0))
        unfunded_gap.append(gap)
        pension_stream.append(pension)
        ss_stream.append(ss)

    total_used_capital = sum(used_capital)
    return used_capital, remaining_capital, unfunded_gap, pension_stream, ss_stream, total_used_capital


def run_step_4(tab4):
    import matplotlib.pyplot as plt
    import numpy as np
    import streamlit as st
    from chronic_module import get_chronic_multiplier
    import pandas as pd
    import matplotlib.ticker as mticker

    def format_thousands(x, _):
        return f"{int(round(x / 1000))}"

    with tab4:
        st.header("Step 4: Financial Outlook")
        st.image("Tuku_Analyst.png", width=60)
        st.markdown(
            "Most household expenses drop after retirement — but healthcare costs often **rise exponentially**. They typically increase from about **8% to over 14% of household spending** as people age, due to chronic conditions, specialist visits, and medications. As you review your financials, pay attention to potential funding gaps in funding your retirement. Planning ahead also helps you preserve your quality of life, covering both essential care and your retirement dreams — including that bucket list you've been meaning to explore.")

        # Load projections from session state
        income_proj = st.session_state.get("income_proj", [])
        savings_proj = st.session_state.get("savings_proj", [])
        proj_401k_user = st.session_state.get("proj_401k", [])
        proj_401k_partner = st.session_state.get("proj_401k_partner", [])

        # --- Inserted logic to construct income_proj accurately across retirement ---
        # --- Fixed: Ensure income_proj spans from current_age to retirement_age, then drops ---
        pension_user = st.session_state.get("pension_user", 0)
        pension_partner = st.session_state.get("pension_partner", 0)
        current_age = st.session_state.get("age", 30)
        retirement_age = 65
        years = st.session_state.get("projection_years", 60)  # Optional fallback

        # Pad or initialize income_proj

        retirement_index = retirement_age - current_age
        if 0 <= retirement_index - 1 < len(income_proj):
            final_income = income_proj[retirement_index - 1]
        else:
            final_income = income_proj[-1] if income_proj else 0

        def pad_array(arr, length, force_negative=False):
            padded = arr + [0] * (length - len(arr))
            return [-abs(x) for x in padded] if force_negative else padded

        # Ensure income_proj is at least `years` long before applying retirement logic
        income_proj = pad_array(income_proj, years)

        for i in range(years):
            age = current_age + i
            if age == retirement_age:
                income_proj[i] = final_income
            elif age > retirement_age:
                income_proj[i] = (final_income * 0.40) + pension_user + pension_partner

        # Merge proj_401k_user and proj_401k_partner with explicit handling of missing/empty lists
        if proj_401k_user is None:
            proj_401k_user = []
        if proj_401k_partner is None:
            proj_401k_partner = []

        def pad_array(arr, length, force_negative=False):
            padded = arr + [0] * (length - len(arr))
            return [-abs(x) for x in padded] if force_negative else padded

        # Extend shorter list to match longer one with 0s, padded before merging
        max_len = max(len(proj_401k_user), len(proj_401k_partner))
        proj_401k_user = pad_array(proj_401k_user, max_len)
        proj_401k_partner = pad_array(proj_401k_partner, max_len)

        proj_401k = [u + p for u, p in zip(proj_401k_user, proj_401k_partner)]
        household_proj = st.session_state.get("household_proj", [])
        current_age = st.session_state.get("age", 30)

        # Retrieve chronic condition multiplier
        user_chronic_count = st.session_state.get("user_chronic_count", "None").lower().replace(" ", "_")
        chronic_multiplier = get_chronic_multiplier(current_age, user_chronic_count)

        # Unified post-retirement logic for savings_proj, proj_401k, and household_proj
        if current_age is not None:
            retirement_age = 65
            savings_growth_rate = st.session_state.get("savings_growth_rate", 0.03)
            k401_growth_rate = st.session_state.get("401k_growth_rate", 0.03)
            # household_growth_rate = st.session_state.get("expense_inflation", 0.025)

            retirement_index = retirement_age - current_age
            retirement_savings_value = savings_proj[retirement_index] if 0 <= retirement_index < len(
                savings_proj) else 0
            retirement_401k_value = proj_401k[retirement_index] if 0 <= retirement_index < len(proj_401k) else 0
            base_post_retirement_household = household_proj[retirement_index] * 0.85 if 0 <= retirement_index < len(
                household_proj) else None

            # Add post-retirement income adjustment similar to other projections
            # retirement_income_value = income_proj[retirement_index] if 0 <= retirement_index < len(income_proj) else 0

            for i in range(len(savings_proj)):
                age = current_age + i
                # Only apply drop for savings, 401k, and household starting at age > retirement_age (i.e., age 66+)
                if age <= retirement_age:
                    continue

                years_post = age - retirement_age

                # Savings
                savings_proj[i] = retirement_savings_value * ((1 + savings_growth_rate) ** years_post)

                # 401(k)
                proj_401k[i] = retirement_401k_value * ((1 + k401_growth_rate) ** years_post)

                # Household
                if i < len(household_proj):
                    if years_post == 1:
                        household_proj[i] = household_proj[i] * 0.85
                        base_post_retirement_household = household_proj[i]
                    elif years_post > 1 and base_post_retirement_household is not None:
                        household_proj[i] = base_post_retirement_household * ((1 - 0.01) ** (years_post - 1))

        monthly_debt = st.session_state.get("monthly_debt", 0)
        premiums = st.session_state.get("premiums", [])
        oop = st.session_state.get("oop", [])

        # --- Fallback logic: ensure arrays are lists before using in years calculation ---
        income_proj = income_proj if isinstance(income_proj, list) else []
        savings_proj = savings_proj if isinstance(savings_proj, list) else []
        proj_401k = proj_401k if isinstance(proj_401k, list) else []
        household_proj = household_proj if isinstance(household_proj, list) else []
        premiums = premiums if isinstance(premiums, list) else []
        oop = oop if isinstance(oop, list) else []

        # Apply chronic multiplier to healthcare costs, but skip premiums if uninsured
        insurance_type = st.session_state.get("insurance_type", "Employer-based")
        if insurance_type == "None":
            premiums = [0] * len(premiums)
        else:
            premiums = [p * chronic_multiplier for p in premiums]
        if oop:
            oop = [o * chronic_multiplier for o in oop]

        # --- Set fallback years ---
        fallback_years = 85

        # --- Inflation Rate ---
        inflation_rate = st.session_state.get("expense_inflation", 0.025)

        # --- Monthly Debt ---
        monthly_debt = st.session_state.get("monthly_debt", 0)

        # --- Provisional debt projection (temporary) ---
        debt_projection = [monthly_debt * ((1 + inflation_rate) ** i) for i in range(fallback_years)]

        # --- Provisional projection array grouping (pre-alignment) ---
        projection_arrays = [income_proj, savings_proj, proj_401k, household_proj, debt_projection, premiums, oop]
        labels = ["Income", "Savings", "401(k)", "Household", "Debt", "Premiums", "OOP"]

        # --- Missing check before alignment ---
        empty_arrays = [label for label, arr in zip(labels, projection_arrays) if not arr]
        if empty_arrays:
            st.error(f"❌ Missing data in: {', '.join(empty_arrays)}. Please revisit earlier steps.")
            return

        # --- Calculate unified final_years ---
        valid_lengths = [len(arr) for arr in projection_arrays]
        final_years = min(fallback_years, *valid_lengths)

        # --- ✅ REDEFINE debt_projection now that final_years is known ---
        debt_projection = [monthly_debt * ((1 + inflation_rate) ** i) for i in range(final_years)]

        # --- Re-pad all arrays to final_years ---
        income_proj = pad_array(income_proj, final_years)
        savings_proj = pad_array(savings_proj, final_years)
        proj_401k = pad_array(proj_401k, final_years)
        household_proj = pad_array(household_proj, final_years)
        debt_projection = pad_array(debt_projection, final_years, force_negative=True)
        premiums = pad_array(premiums, final_years)
        oop = pad_array(oop, final_years)

        # --- Final grouped arrays for validation ---
        projection_arrays = [income_proj, savings_proj, proj_401k, household_proj, debt_projection, premiums, oop]
        labels = ["Income", "Savings", "401(k)", "Household", "Debt", "Premiums", "OOP"]



        # ✅ This is the only correct place to set ages
        ages = list(range(current_age, current_age + final_years))

        # Rebuild income_proj only if it's missing or misaligned
        starting_income = st.session_state.get("net_user_income", 0) * 12
        if not income_proj or len(income_proj) != final_years:
            income_proj = [starting_income * ((1 + 0.02) ** i) for i in range(final_years)]

        # Apply retirement transition logic to income_proj
        retirement_index = 65 - current_age
        if 0 <= retirement_index - 1 < len(income_proj):
            final_income = income_proj[retirement_index - 1]
        else:
            final_income = income_proj[-1] if income_proj else 0

        for i in range(final_years):
            age = current_age + i
            if age == 65:
                income_proj[i] = final_income
            elif age > 65:
                income_proj[i] = (final_income * 0.40) + pension_user + pension_partner

        # Surplus/Deficit Over Time
        total_expenses = [household_proj[i] + premiums[i] + oop[i] for i in range(final_years)]
        surplus = [income_proj[i] - total_expenses[i] for i in range(final_years)]

        # capital_graph_df = st.session_state.get("capital_graph_df", pd.DataFrame())
        # expense_df = st.session_state.get("expense_df", pd.DataFrame())



        # Side-by-side Graphs: Annual Expenditures, Income, Savings + 401(k)
        if not ages or not all(len(arr) == len(ages) for arr in
                               [household_proj, debt_projection, premiums, oop, income_proj, savings_proj, proj_401k]):
            st.error("⚠️ Data mismatch: Please ensure Step 2 has been completed and submitted.")
            return

        # All three charts in one row
        fig, axs = plt.subplots(1, 3, figsize=(24, 5))

        # Annual Expenditures (stacked)
        axs[0].bar(ages, household_proj, label='Household')
        bottom_premiums = np.array(household_proj)
        axs[0].bar(ages, premiums, bottom=bottom_premiums, label='Premiums')
        bottom_oop = bottom_premiums + np.array(premiums)
        axs[0].bar(ages, oop, bottom=bottom_oop, label='OOP')
        axs[0].set_title("Annual Expenditures Projection")
        axs[0].set_xlabel("Age")
        axs[0].set_ylabel("Amount ($)")
        axs[0].legend()
        axs[0].grid(True)
        axs[0].yaxis.set_major_formatter(mticker.FuncFormatter(format_thousands))
        axs[0].set_ylabel("Amount ($,000)")

        # Annual Income (stacked: Primary Income + Pension)
        pension_user = st.session_state.get("pension_user", 0)
        pension_partner = st.session_state.get("pension_partner", 0)
        total_pension = pension_user + pension_partner
        pension_stream = [0 if age < 66 else total_pension for age in ages]
        primary_income = [max(income_proj[i] - pension_stream[i], 0) for i in range(len(ages))]
        axs[1].bar(ages, income_proj, label="Total Income")
        axs[1].bar(ages, pension_stream, label="Pension Overlay", alpha=0.3)
        axs[1].set_title("Annual Income Projection")
        axs[1].set_xlabel("Age")
        axs[1].yaxis.set_major_formatter(mticker.FuncFormatter(format_thousands))
        axs[1].legend()
        axs[1].grid(True)
        axs[1].set_ylabel("Amount ($,000)")

        # Savings and 401(k)
        axs[2].bar(ages, savings_proj, label="Savings")
        bottom_401k = np.array(savings_proj)
        axs[2].bar(ages, proj_401k, bottom=bottom_401k, label="401(k)")
        axs[2].set_title("Savings and 401(k) Projection")
        axs[2].set_xlabel("Age")
        axs[2].set_ylabel("Amount ($,000)")
        axs[2].yaxis.set_major_formatter(mticker.FuncFormatter(format_thousands))
        axs[2].legend()
        axs[2].grid(True)
        axs[2].axhline(0, color='black', linewidth=0.8)

        st.pyplot(fig)

        # Validate that all required data arrays are non-empty and aligned
        required_data = {
            "Household": household_proj,
            "Premiums": premiums,
            "OOP": oop,
            "Income": income_proj,
            "Savings": savings_proj,
            "401(k)": proj_401k,
            "Debt": debt_projection
        }
        missing_or_misaligned = [
            key for key, arr in required_data.items()
            if not arr or len(arr) != len(ages)
        ]

        if missing_or_misaligned:
            st.warning(f"⚠️ Missing or misaligned data: {', '.join(missing_or_misaligned)}. Skipping export to Step 5.")
            st.session_state["capital_graph_df"] = pd.DataFrame()  # Clear empty or invalid graph data
        else:
            expense_df = pd.DataFrame({
                "Age": ages,
                "Income": income_proj,
                "Household": household_proj,
                "Premiums": premiums,
                "OOP": oop,
                "Total Expenses": total_expenses,
                "Surplus": surplus,
                "Savings": savings_proj,
                "401(k)": proj_401k,
                "Debt": debt_projection
            })
            st.session_state["expense_df"] = expense_df
            st.session_state["surplus"] = surplus
            # Debug print to confirm columns in capital_graph_df
            # print(st.session_state["capital_graph_df"].head())
            st.session_state["capital_graph_df"] = expense_df[["Age", "Savings", "401(k)"]].copy()

        # Note: Removed all logic and graphs tied to the capital care fund as per instructions.

        # --- Lifetime Retirement Income Sources Pie Chart ---
        # Inserted pie chart block before Retirement Readiness
        capital_graph_df = st.session_state.get("capital_graph_df", pd.DataFrame())
        expense_df = st.session_state.get("expense_df", pd.DataFrame())
        if (
                capital_graph_df is not None and not capital_graph_df.empty and
                expense_df is not None and not expense_df.empty and
                st.session_state.get("surplus") is not None
        ):
            age_series = expense_df["Age"].tolist()
            surplus = st.session_state.get("surplus", [])
            if not age_series or not surplus or len(surplus) != len(age_series):
                st.warning("Age or surplus data is missing or mismatched — skipping retirement readiness chart.")
                return

            # Defensive check for required arrays
            income_proj = st.session_state.get("income_proj", [])
            savings_proj = st.session_state.get("savings_proj", [])
            proj_401k_user = st.session_state.get("proj_401k", [])
            proj_401k_partner = st.session_state.get("proj_401k_partner", [])
            if proj_401k_user is None:
                proj_401k_user = []
            if proj_401k_partner is None:
                proj_401k_partner = []
            max_len = max(len(proj_401k_user), len(proj_401k_partner))
            # Only pad and combine 401k arrays, do not modify income_proj
            proj_401k_user_padded = pad_array(proj_401k_user, max_len)
            proj_401k_partner_padded = pad_array(proj_401k_partner, max_len)
            proj_401k_combined = [u + p for u, p in zip(proj_401k_user_padded, proj_401k_partner_padded)]

            # Defensive: ensure income_proj, savings_proj, proj_401k_combined are non-empty and padded
            if not income_proj or not savings_proj or not proj_401k_combined:
                st.warning("Missing required data for retirement readiness calculations.")
                return

            # Align savings_proj to age_series length for charting, but do not modify income_proj
            if savings_proj is None:
                savings_proj = []
            if len(savings_proj) < len(age_series):
                savings_proj = savings_proj + [0] * (len(age_series) - len(savings_proj))
            elif len(savings_proj) > len(age_series):
                savings_proj = savings_proj[:len(age_series)]

            # Additional alignment check and debug chart
            if len(savings_proj) != len(proj_401k_combined):
                st.warning(f"Savings ({len(savings_proj)}) and 401k ({len(proj_401k_combined)}) lengths do not match.")

            if not savings_proj or not proj_401k_combined or len(savings_proj) != len(proj_401k_combined):
                st.warning("Missing or mismatched savings or 401(k) data — skipping retirement readiness chart.")
                return

            # Defensive check for retirement_index
            retirement_age = 65
            current_age = st.session_state.get("age", 30)
            retirement_index = retirement_age - current_age
            if retirement_index < 0 or retirement_index >= len(income_proj):
                st.warning("Retirement index out of bounds. Skipping retirement readiness and income pie chart.")
                return

            col_tuku, col_pie, col_divider, col_bar = st.columns([0.5, 1.3, 0.1, 2])


            # Estimate Social Security and clamp if needed
            final_income = income_proj[retirement_index - 1] if 0 <= retirement_index - 1 < len(income_proj) else 0
            final_income = min(final_income, 500_000)  # Sanity cap
            estimated_ss = final_income * 0.40
            years_post_retirement = len(income_proj) - retirement_index
            estimated_ss_total = estimated_ss * years_post_retirement
            estimated_ss_total = 0 if estimated_ss_total > 1_000_000 else estimated_ss_total

            # Save to session state for Step 5 and downstream charts
            st.session_state["estimated_ss_total"] = estimated_ss_total
            st.session_state["estimated_ss_annual"] = estimated_ss

            savings_total = savings_proj[retirement_index] if 0 <= retirement_index < len(savings_proj) else 0
            proj_401k_val = proj_401k_combined[retirement_index] if 0 <= retirement_index < len(
                proj_401k_combined) else 0
            pension_user = st.session_state.get("pension_user", 0)
            pension_partner = st.session_state.get("pension_partner", 0)
            total_pension = pension_user + pension_partner
            lifetime_pension = total_pension * (len(income_proj) - retirement_index)

            # Calculate additional income after retirement not covered by SS or pensions
            post_retirement_income = sum(income_proj[retirement_index:]) - estimated_ss - lifetime_pension
            if post_retirement_income < 0:
                post_retirement_income = 0

            # Total capital drawn down after retirement

            # Compute drawdown early for use in pie chart
            chart_ages = []
            deficit_values = []
            for i in range(len(age_series)):
                age = age_series[i]
                if age >= 65 and i < len(surplus):
                    chart_ages.append(age)
                    deficit = -surplus[i] if surplus[i] < 0 else 0
                    deficit_values.append(deficit)

            used_capital, _, _, _, _, total_used_capital = compute_retirement_drawdown(
                chart_ages, deficit_values, savings_proj, proj_401k_combined,
                retirement_index, total_pension, estimated_ss
            )

            # Retrieve snapshot values at retirement


            years_post_retirement = len(income_proj) - retirement_index
            estimated_ss_total = estimated_ss * years_post_retirement

            savings_total = savings_proj[retirement_index] if 0 <= retirement_index < len(savings_proj) else 0
            proj_401k_val = proj_401k_combined[retirement_index] if 0 <= retirement_index < len(
                proj_401k_combined) else 0

            labels = ["Social Security", "Cash Savings at Retirement", "401(k) at Retirement", "Pension Income"]
            values = [estimated_ss_total, savings_total, proj_401k_val, lifetime_pension]

            with col_tuku:
                st.image("Tuku_Analyst.png", width=60)

            with col_pie:
                # Filter out sources with 0 value for cleaner pie chart
                combined_sources = list(zip(labels, values))
                filtered_sources = [(label, val) for label, val in combined_sources if val > 0]
                if not filtered_sources:
                    st.info("No retirement income sources available to display.")
                else:
                    filtered_labels, filtered_values = zip(*filtered_sources)
                    st.markdown("#### Retirement Income Sources")
                    fig_pie, ax_pie = plt.subplots(figsize=(1.8, 1.8))

                    def filter_autopct(pct):
                        return f"{pct:.1f}%" if pct > 2 else ''

                    wedges, texts, autotexts = ax_pie.pie(
                        filtered_values,
                        labels=filtered_labels,
                        autopct=filter_autopct,
                        startangle=90,
                        textprops={'fontsize': 7}
                    )
                    ax_pie.axis('equal')
                    st.pyplot(fig_pie)



            with col_divider:
                st.markdown("<div style='height: 160px; border-left: 1px solid #ccc;'></div>", unsafe_allow_html=True)

            with col_bar:
                st.markdown("<div style='text-align: center;'><h4>Retirement Readiness</h4></div>",
                            unsafe_allow_html=True)
                st.markdown(
                    "This projection helps you plan ahead so you don’t outlive your financial resources — including savings, 401(k), and any eligible pension.")
                # Always render retirement readiness chart for all post-retirement years, even with zero deficits
                chart_ages = []
                deficit_values = []
                for i in range(len(age_series)):
                    age = age_series[i]
                    if age >= 65 and i < len(surplus):
                        chart_ages.append(age)
                        deficit = -surplus[i] if surplus[i] < 0 else 0
                        deficit_values.append(deficit)

                if chart_ages:
                    savings_total = savings_proj[retirement_index] if 0 <= retirement_index < len(savings_proj) else 0
                    proj_401k_val = proj_401k_combined[retirement_index] if 0 <= retirement_index < len(
                        proj_401k_combined) else 0
                    total_pension = pension_user + pension_partner
                    ss_per_year = estimated_ss / len(chart_ages)
                    current_capital = savings_total + proj_401k_val

                    used_capital = []
                    remaining_capital = []
                    unfunded_gap = []
                    pension_stream = []
                    ss_stream = []

                    for i, age in enumerate(chart_ages):
                        pension = total_pension  # annual pension
                        ss = ss_per_year
                        total_income = pension + ss

                        # Actual deficit to cover (if surplus < 0)
                        deficit = deficit_values[i]
                        uncovered = max(deficit - total_income, 0)

                        used = min(uncovered, current_capital)
                        gap = max(uncovered - used, 0)
                        current_capital -= used

                        used_capital.append(used)
                        remaining_capital.append(max(current_capital, 0))
                        unfunded_gap.append(gap)
                        pension_stream.append(pension)
                        ss_stream.append(ss)

                    df_drawdown = pd.DataFrame({
                        "Age": chart_ages,
                        "Capital Drawn (Savings/401k)": used_capital,
                        "Remaining Capital": remaining_capital,
                        "Unfunded Gap": unfunded_gap,
                        "Pension Income": pension_stream,
                        "Social Security": ss_stream
                    }).set_index("Age")

                    total_used_capital = sum(used_capital) if 'used_capital' in locals() else 0


                    # Retirement Readiness Indicator (revised logic)
                    st.subheader("🎯 Retirement Readiness")
                    if surplus and capital_graph_df is not None and not capital_graph_df.empty:
                        age_series = expense_df["Age"].tolist()
                        chart_ages = []
                        deficit_values = []
                        for i, age in enumerate(age_series):
                            if age >= 65 and i < len(surplus):
                                chart_ages.append(age)
                                deficit = -surplus[i] if surplus[i] < 0 else 0
                                deficit_values.append(deficit)

                        if chart_ages:
                            savings_total = st.session_state.get("savings_projection", [0])[-1]
                            proj_401k = st.session_state.get("proj_401k", [0])[-1]
                            pension_user = st.session_state.get("pension_user", 0)
                            pension_partner = st.session_state.get("pension_partner", 0)
                            total_pension = pension_user + pension_partner
                            total_available = savings_total + proj_401k + (total_pension * len(chart_ages))

                            used_capital = []
                            remaining_capital = []
                            unfunded_gap = []
                            current_capital = total_available

                            for deficit in deficit_values:
                                if deficit > 0:
                                    used = min(deficit, current_capital)
                                    gap = max(deficit - used, 0)
                                    current_capital -= used
                                else:
                                    used = 0
                                    gap = 0
                                used_capital.append(used)
                                remaining_capital.append(max(current_capital, 0))
                                unfunded_gap.append(gap)

                            surplus_remaining = remaining_capital.copy()

                            df_drawdown = pd.DataFrame({
                                "Age": chart_ages,
                                "Capital Drawn from 401k/Savings": used_capital,
                                "Remaining Capital": surplus_remaining,
                                "Remaining Deficit": unfunded_gap
                            }).set_index("Age")

                            st.bar_chart(df_drawdown, use_container_width=True)

                            if any(used_capital):
                                if current_capital > 0:
                                    st.success(
                                        "✅ Your available capital is projected to cover all retirement expenses.")
                                else:
                                    depletion_age = chart_ages[
                                        len(used_capital) - remaining_capital[::-1].index(
                                            0) - 1] if 0 in remaining_capital else \
                                        chart_ages[-1]
                                    st.warning(
                                        f"⚠️ You may fall short by approximately ${-current_capital:,.0f} in retirement funding. Capital is projected to be depleted by age {depletion_age}.")
                            else:
                                st.info(
                                    "✅ No capital drawdown was needed. You remain financially self-sufficient through retirement.")
                    else:
                        st.info(
                            "ℹ️ Retirement readiness analysis is incomplete. Missing data for surplus or capital projections.")

                    # Estimate Social Security: 40% of final pre-retirement income times years post-retirement
                    final_income = income_proj[retirement_index - 1] if 0 <= retirement_index - 1 < len(
                        income_proj) else 0
                    estimated_ss = final_income * 0.40 * (len(income_proj) - retirement_index)

                    # Retrieve final projected values (at retirement_index)
                    savings_total = savings_proj[retirement_index] if 0 <= retirement_index < len(savings_proj) else 0
                    proj_401k_val = proj_401k_combined[retirement_index] if 0 <= retirement_index < len(
                        proj_401k_combined) else 0
                    pension_user = st.session_state.get("pension_user", 0)
                    pension_partner = st.session_state.get("pension_partner", 0)
                    total_pension = pension_user + pension_partner
                    lifetime_pension = total_pension * (len(income_proj) - retirement_index)

                    labels = ["Social Security (est.)", "Savings", "401(k)", "Pensions"]
                    values = [estimated_ss, savings_total, proj_401k_val, lifetime_pension]


                else:
                    st.warning("No post-retirement years available for readiness chart.")
        else:
            st.warning("Capital or expense data missing — skipping retirement readiness chart.")


