import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from chronic_module import get_chronic_multiplier

def run_step_5(tab6):
    with tab6:
        st.header("Protect your Healthcare with a Capital Care Plan.")

        # Summary Overview
        profile = st.session_state.get("profile", {})
        health_status = profile.get("health_status", "Unknown").title()
        family_history = profile.get("family_history", False)
        drawdown_option = st.session_state.get("drawdown_option", "Not selected")
        available_income = st.session_state.get("net_income_monthly", 0)
        savings_balance = st.session_state.get("savings_balance", 0)
        recommendation_text = st.session_state.get("recommendation_text", "")

        st.subheader("🧾 Summary Overview")
        user_age = profile.get("age", 30)
        partner_age = st.session_state.get("partner_age", 0)
        partner_health_status = st.session_state.get("partner_health_status", None)
        family_status = profile.get("family_status", "single")
        savings_balance = st.session_state.get("savings_balance", 0)
        net_income_monthly = st.session_state.get("net_income_monthly", 0)

        profile_summary = f"- **👤 Profile**: {health_status}"
        if family_status == "family" and partner_health_status:
            profile_summary += f", Partner: {partner_health_status.title()}"
        if family_history:
            profile_summary += ", Family History: Yes"
        else:
            profile_summary += ", Family History: No"

        st.markdown(f"<p style='font-size: 15px;'><strong>👤 Profile:</strong> {profile_summary[17:]}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 15px;'><strong>💰 Financial Path:</strong> Income: ${net_income_monthly:,.0f}/mo, Savings: ${savings_balance:,.0f}</p>", unsafe_allow_html=True)

        user_age = st.session_state.get("profile", {}).get("age", 30)
        user_chronic_count = st.session_state.get("user_chronic_count", "None").lower().replace(" ", "_")
        chronic_multiplier = get_chronic_multiplier(user_age, user_chronic_count)
        expense_df = st.session_state.get("expense_df", pd.DataFrame())
        # Restore columns from session state if missing
        if "Premium" not in expense_df.columns:
            if "premiums" in st.session_state:
                expense_df["Premium"] = st.session_state["premiums"][:len(expense_df)]
            elif "projections" in st.session_state and "premiums" in st.session_state["projections"]:
                expense_df["Premium"] = st.session_state["projections"]["premiums"][:len(expense_df)]
        if "OOP" not in expense_df.columns and "oop" in st.session_state.get("projections", {}):
            expense_df["OOP"] = st.session_state["projections"]["oop"][:len(expense_df)]
        if "Household" not in expense_df.columns and "household" in st.session_state.get("projections", {}):
            expense_df["Household"] = st.session_state["projections"]["household"][:len(expense_df)]
        if "Age" not in expense_df.columns:
            expense_df["Age"] = list(range(user_age, user_age + len(expense_df)))

        if "OOP" in expense_df.columns:
            expense_df["OOP"] = expense_df["OOP"] * chronic_multiplier
        if "Premium" in expense_df.columns:
            expense_df["Premium"] = expense_df["Premium"] * chronic_multiplier

        average_healthcare_pct = None

        capital_graph_df = st.session_state.get("capital_graph_df", pd.DataFrame())
        surplus = st.session_state.get("surplus", [])
        if st.session_state.get("debug_mode", False):
            st.write("Surplus preview:", surplus[:5])
            st.write("Capital DF preview:", capital_graph_df.head())
        cumulative_surplus = st.session_state.get("cumulative_surplus", [])
        risk_ratio = st.session_state.get("risk_trajectory", [])
        lifetime_risk = st.session_state.get("lifetime_health_risk_ratio", 0)

        # Display summary metrics
        st.subheader("📊 Key Metrics")
        col1, col2 = st.columns(2)
        col1.metric("Lifetime Health Risk", f"{lifetime_risk:.0%}")
        if lifetime_risk > 0.6:
            st.markdown("- Your lifetime health risk is **high**. This includes personal or family predispositions. Consider prioritizing preventive and capital-based health strategies.")
        elif lifetime_risk > 0.3:
            st.markdown("- Your health risk is moderate. Watch for potential blind spots in your or your family's medical history.")

        # Healthcare Expense Ratio Over Time
        if not expense_df.empty:
            required_columns = ["OOP", "Premium", "Household"]
            missing_columns = [col for col in required_columns if col not in expense_df.columns]
            if missing_columns:
                st.warning(f"Missing data for: {', '.join(missing_columns)}. Step 5 cannot fully display summary metrics.")
                return

            expense_df["Healthcare"] = expense_df["OOP"] + expense_df["Premium"]
            expense_df["Total"] = expense_df["OOP"] + expense_df["Premium"] + expense_df["Household"]
            expense_df["Healthcare %"] = (expense_df["Healthcare"] / expense_df["Total"]) * 100
            if "Healthcare %" in expense_df.columns:
                average_healthcare_pct = expense_df["Healthcare %"].mean()
                st.session_state["average_healthcare_pct"] = average_healthcare_pct
                current_healthcare_pct = expense_df.iloc[0]["Healthcare %"]

                # --- Pie charts block ---
                import matplotlib.pyplot as plt

                col_l, col_divider, col_m, col_r = st.columns([1.2, 0.1, 1.2, 1.2])

                with col_l:
                    st.markdown("**Lifetime Health Risk**")
                    fig_lifetime, ax_lifetime = plt.subplots(figsize=(1.5, 1.5))
                    wedges, texts, autotexts = ax_lifetime.pie(
                        [lifetime_risk, 1 - lifetime_risk],
                        labels=["", ""],
                        autopct=lambda pct: f"{lifetime_risk:.0%}" if pct > 1 and pct > 50 else "",
                        startangle=90,
                        colors=["#ff9999", "#f0f0f0"],
                        textprops={'fontsize': 6, 'weight': 'bold'}
                    )
                    for txt in texts:
                        txt.set_text("")
                    for i, autotxt in enumerate(autotexts):
                        autotxt.set_text(f"{lifetime_risk:.0%}" if i == 0 else "")
                    ax_lifetime.axis("equal")
                    st.pyplot(fig_lifetime)

                with col_divider:
                    st.markdown("<div style='height: 120px; border-left: 1px solid #ccc;'></div>", unsafe_allow_html=True)

                with col_m:
                    st.markdown("**Current Healthcare % of Total Expenses:**")
                    fig_cur, ax_cur = plt.subplots(figsize=(1.5, 1.5))
                    wedges, texts, autotexts = ax_cur.pie(
                        [current_healthcare_pct / 100, 1 - (current_healthcare_pct / 100)],
                        labels=["", ""],
                        autopct=lambda pct: f"{current_healthcare_pct:.0f}%" if pct > 1 and pct > 50 else "",
                        startangle=90,
                        colors=["#66b3ff", "#f0f0f0"],
                        textprops={'fontsize': 6, 'weight': 'bold'}
                    )
                    for txt in texts:
                        txt.set_text("")
                    for i, autotxt in enumerate(autotexts):
                        autotxt.set_text(f"{current_healthcare_pct:.0f}%" if i == 0 else "")
                    ax_cur.axis("equal")
                    st.pyplot(fig_cur)

                with col_r:
                    st.markdown("**Average Healthcare % of Total Expenses:**")
                    fig_avg, ax_avg = plt.subplots(figsize=(1.5, 1.5))
                    wedges, texts, autotexts = ax_avg.pie(
                        [average_healthcare_pct / 100, 1 - (average_healthcare_pct / 100)],
                        labels=["", ""],
                        autopct=lambda pct: f"{average_healthcare_pct:.0f}%" if pct > 1 and pct > 50 else "",
                        startangle=90,
                        colors=["#99ff99", "#f0f0f0"],
                        textprops={'fontsize': 6, 'weight': 'bold'}
                    )
                    for txt in texts:
                        txt.set_text("")
                    for i, autotxt in enumerate(autotexts):
                        autotxt.set_text(f"{average_healthcare_pct:.0f}%" if i == 0 else "")
                    ax_avg.axis("equal")
                    st.pyplot(fig_avg)

                st.image("Tuku_Analyst.png", width=64)
                st.markdown("Your average healthcare spending is 12.5%, which is above the national benchmark of 8%. Consider reviewing your care plan or insurance.")

        # Retirement Readiness Indicator (revised logic)
        st.subheader("🎯 Retirement Readiness")
        if surplus and capital_graph_df is not None and not capital_graph_df.empty:
            age_series = expense_df["Age"].tolist()
            # Updated drawdown logic from Step 4
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
                        st.success("✅ Your available capital is projected to cover all retirement expenses.")
                    else:
                        depletion_age = chart_ages[len(used_capital) - remaining_capital[::-1].index(0) - 1] if 0 in remaining_capital else chart_ages[-1]
                        st.warning(f"⚠️ You may fall short by approximately ${-current_capital:,.0f} in retirement funding. Capital is projected to be depleted by age {depletion_age}.")
                else:
                    st.info("✅ No capital drawdown was needed. You remain financially self-sufficient through retirement.")
        else:
            st.info("ℹ️ Retirement readiness analysis is incomplete. Missing data for surplus or capital projections.")

        # Smart Callouts
        st.subheader("📌 Smart Callouts")
        if lifetime_risk > 0.6:
            st.markdown("- Your projected lifetime health risk is **high**. Consider boosting your capital care fund early.")
        if cumulative_surplus and min(cumulative_surplus) < 0:
            st.markdown("- You may face cumulative deficits. Review your expenses or increase income/savings.")
        if not capital_graph_df.empty and "Capital Used" in capital_graph_df.columns and capital_graph_df["Capital Used"].sum() == 0:
            st.markdown("- Your capital fund was unused. Consider reallocating future contributions.")
        if isinstance(average_healthcare_pct, (int, float)) and lifetime_risk > 0.3 and average_healthcare_pct > 8:
            st.markdown("- Given both elevated risk and spending, consider planning alternate funding sources such as capital care, HSA, or targeted insurance.")
        st.markdown("Use this summary to evaluate your long-term health and financial readiness.")

    # Completion and Navigation to Step 6
    st.markdown("---")
    with st.info("### 👣 Ready to Continue?", icon="ℹ️"):
        col1, col2 = st.columns([1, 9])
        with col1:
            st.image("Tuku_Winking.png", width=48)
        with col2:
            proceed = st.radio("Do you want to continue to Step 6?", ["Not Now", "Yes"], key="proceed_to_ai")
    if proceed == "Yes":
        st.session_state["step5_submitted"] = True