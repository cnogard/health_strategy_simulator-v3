import streamlit as st
from projected_health_risk import get_risk_insight
from simulator_core import simulate_capital_allocation
import json
import pandas as pd


def recommend_insurance_strategy(profile, surplus, insurance_type, capital_shift):
    """
    Suggests whether to adjust insurance based on surplus and capital opportunity.
    """
    health_status = profile.get("health_status", "healthy")
    age = profile.get("age", 30)

    recommendations = []

    if insurance_type == "None":
        if surplus > 5000 and health_status == "healthy":
            recommendations.append("🛡️ You're uninsured but healthy and have a surplus — consider catastrophic or basic insurance + capital care fund.")
        else:
            recommendations.append("❗ Consider at least minimal insurance to protect against unexpected events.")

    elif insurance_type in ["Employer", "Marketplace"]:
        if capital_shift > 10000:
            recommendations.append("💡 Consider reducing insurance level and allocating saved premiums into capital care.")
        if surplus < 0:
            recommendations.append("📉 Your costs exceed income — review your insurance costs or care usage.")
        elif health_status == "healthy" and age < 45:
            recommendations.append("🔄 You may be over-insured — explore digital-first care or high-deductible plans.")

    if health_status == "high":
        recommendations.append("⚠️ Due to high health risk, maintain sufficient insurance or ensure capital reserves.")

    if not recommendations:
        recommendations.append("✅ Your insurance strategy looks appropriate for your profile.")

    return recommendations


# --- Recommendation Generation Function ---
def generate_recommendation(
    profile,
    insurance_type,
    surplus,
    capital_strategy,
    risk_trajectory,
    family_risk_summary,
    high_risk_score
):
    # Ensure risk_trajectory is displayed for user if available
    if "risk_trajectory" not in st.session_state:
        st.session_state["risk_trajectory"] = risk_trajectory
    recs = []

    # Move risk insight logic to the top, always add if present
    insight = get_risk_insight(profile.get("age"), profile.get("health_status"))
    if insight:
        recs.append("🧠 " + insight)
        # Add user-specific health risk trajectory chart if available
        if risk_trajectory and isinstance(risk_trajectory, list):
            risk_df = pd.DataFrame({
                "Age": list(range(profile["age"], profile["age"] + len(risk_trajectory))),
                "User Risk": risk_trajectory
            }).set_index("Age")
            st.line_chart(risk_df)

    # Risk insights
    if risk_trajectory:
        max_risk = max(risk_trajectory)
        if max_risk >= 0.9:
            recs.append("⚠️ Your projected health risk becomes very high in later years. Consider planning for increased medical costs.")

    if high_risk_score and high_risk_score > 7:
        recs.append("📌 You or a family member may be considered high-risk. Ensure you maintain sufficient savings or high-deductible coverage.")

    if family_risk_summary:
        if family_risk_summary.get("high_risk_dependents", 0) > 0:
            recs.append("🧒 One or more dependents have high risk—pediatric or long-term planning may be necessary.")

    # Financial strategy
    # Ensure surplus is a flat list for consistent checks
    if isinstance(surplus, list):
        flattened_surplus = [item for sublist in surplus for item in (sublist if isinstance(sublist, list) else [sublist])]
    else:
        flattened_surplus = [surplus]

    if isinstance(flattened_surplus, list) and any(s < 0 for s in flattened_surplus):
        recs.append("💸 You may have a healthcare deficit in future years. Consider increasing income or reducing expenses.")
    else:
        recs.append("💰 You're generating surplus — consider allocating a portion toward a capital care fund.")

    if insurance_type in ["Marketplace", "Employer"] and profile.get("health_status") == "healthy":
        recs.append("🔄 You may benefit from reallocating a portion of your insurance premiums to capital care, especially if you're low-risk or underutilizing current coverage.")

    if capital_strategy and capital_strategy.get("long", 0) > 0.5:
        recs.append("📈 Strong long-term capital investment strategy in place. Monitor market conditions and rebalance annually.")

    recs.append("✅ Revisit this simulation yearly or after major life changes to stay on track.")

    return recs


tab1, tab2, tab3, tab4 = st.tabs(["Step 1: Profile", "Step 2: Financials", "Step 3: Simulation", "Step 4: AI Recommendation"])

with tab1:
    uploaded_file = st.file_uploader("Upload Previous Simulation", type=["json"])
    if uploaded_file is not None:
        uploaded_data = json.load(uploaded_file)
        st.session_state["uploaded_simulation"] = uploaded_data
        st.success("✅ Simulation file uploaded successfully.")

    # Logic for Step 1: Profile
    if st.session_state.get("step1_submitted"):
        # Existing profile submission handling code here
        pass

with tab2:
    # Logic for Step 2: Financials
    if st.session_state.get("step2_submitted"):
        # Existing financials submission handling code here
        pass

with tab3:
    # Logic for Step 3: Simulation
    if st.session_state.get("step3_submitted"):
        # Existing simulation submission handling code here
        pass

with tab4:
    if st.session_state.get("step4_submitted"):
        profile = st.session_state.get("profile", {})
        insurance_type = st.session_state.get("insurance_type", "None")
        cost_df = st.session_state.get("cost_df", None)

        st.subheader("📌 General Recommendation")
        st.markdown("✅ Displayed general recommendations")


        recs = st.session_state.get("recs", [])
        st.subheader("🧭 Personalized Recommendations")
        if recs:
            for rec in recs:
                if "📌 capital shift" in rec.lower() or "capital_shift" in rec.lower():
                    continue
                st.markdown(f"- {rec}")
        else:
            st.markdown("No personalized recommendations to display.")

        st.subheader("🧮 Capital Strategy Options")

        st.markdown("### Option 1: 💰 Allocate Funds from Savings or Income")
        fund_source = st.radio("Where would you like to draw capital funds from?", ["From Existing Savings", "From Monthly Income"])
        if fund_source == "From Existing Savings":
            st.markdown("✅ Capital allocation from savings selected")
            allocate_from_savings = st.slider("% of Current Savings to Allocate", 0, 100, 20)
            new_fund_contribution = 0
        else:
            st.markdown("✅ Capital allocation from income selected")
            new_fund_contribution = st.number_input("Monthly Contribution to Capital Health Fund ($)", min_value=0, value=200)
            allocate_from_savings = 0

            net_income_monthly = st.session_state.net_income_monthly
            monthly_expenses = st.session_state.monthly_expenses
            debt_payment = st.session_state.debt_monthly_payment
            monthly_oop = cost_df["OOP Cost"].iloc[0] / 12 if cost_df is not None else 0
            free_cash = net_income_monthly - monthly_expenses - debt_payment - monthly_oop
            st.markdown(f"💡 Estimated Free Cash: **${free_cash:,.0f}/month**")
            if new_fund_contribution > free_cash:
                st.warning("⚠️ Contribution exceeds your free cash. Please review your inputs.")

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

        capital_invest_toggle = st.radio("Do you want to evaluate how a dedicated Capital Care Investment strategy can help you meet your objectives?", ["No", "Yes"], key="capital_invest_toggle")

        if capital_invest_toggle == "Yes":
            with st.expander("💼 Capital Investment Allocation", expanded=True):
                st.markdown("This section helps you decide how to allocate available funds to your capital care fund.")
                st.markdown("You can allocate a portion of your **existing savings** and/or set up **new monthly contributions**.")
                st.markdown("✅ Captured short-term investment allocation")
                short_term = st.slider("% Short-Term", 0, 100, 10)
                max_mid_term = 100 - short_term
                mid_term = st.slider("% Mid-Term", 0, max_mid_term, 20)
                long_term = 100 - short_term - mid_term
                st.markdown(f"📈 Long-Term automatically set to: **{long_term}%**")

                st.session_state.capital_fund_source = fund_source
                st.session_state.capital_from_savings_pct = allocate_from_savings
                st.session_state.capital_monthly_contrib = new_fund_contribution
                cap_alloc = {
                    "short": short_term / 100,
                    "mid": mid_term / 100,
                    "long": long_term / 100
                }
                st.session_state.cap_alloc = cap_alloc

                run_capital_sim = st.button("Run Capital Investment Strategy")
                if run_capital_sim:
                    # --- Simulate investment strategy and show adjusted projections ---
                    capital_strategy = st.session_state.cap_alloc
                    cost_df = st.session_state.cost_df

                    # Determine actual initial capital from both savings and premium shift
                    current_savings = st.session_state.get("current_savings", 0)
                    allocate_pct = st.session_state.get("capital_from_savings_pct", 0)
                    premium_realloc = st.session_state.get("insurance_savings", 0)

                    if fund_source == "From Existing Savings":
                        initial_capital = current_savings * allocate_pct / 100 + premium_realloc
                    else:
                        initial_capital = new_fund_contribution * 12 + premium_realloc

                    monthly_contrib = st.session_state.get("capital_monthly_contrib", 0)

                    if "Capital+OOP" in cost_df.columns:
                        annual_healthcare_costs = cost_df["Capital+OOP"]
                    elif "Healthcare Cost" in cost_df.columns:
                        annual_healthcare_costs = cost_df["Healthcare Cost"]
                    else:
                        st.error("❌ Missing expected cost columns in cost_df.")
                        st.stop()

                    updated_df = simulate_capital_allocation(
                        cost_df=cost_df,
                        strategy_allocation=capital_strategy,
                        initial_capital=initial_capital,
                        monthly_contribution=monthly_contrib,
                        fund_source="Combined",
                        pct_from_savings=allocate_pct,
                        annual_healthcare_costs=annual_healthcare_costs
                    )

                    st.session_state.updated_cost_df = updated_df

                    st.subheader("📉 Adjusted Healthcare and Financial Projections")

                    # Compute capital-enhanced surplus
                    original_surplus = st.session_state.expense_df["Surplus/Deficit"].tolist()
                    cap_alloc = updated_df["Net Surplus After Capital"].tolist()
                    after_capital_strategy = [s + c if s > 0 else s for s, c in zip(original_surplus, cap_alloc)]

                    ages = st.session_state.expense_df["Age"]
                    income_savings = st.session_state.expense_df["Income + Savings"]
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

                    # Capital shift summary
                    capital_shift = updated_df["Capital Shift"].iloc[-1] if "Capital Shift" in updated_df.columns else 0
                    st.markdown("### 💸 Capital Shift Summary")
                    st.markdown(
                        f"<strong>📌 Capital Shift (Lifetime Projection):</strong> &nbsp;&nbsp;<strong>${capital_shift:,.0f}</strong>",
                        unsafe_allow_html=True
                    )
                    user_age = st.session_state.get("profile", {}).get("age", 30)
                    st.caption(
                        f"Note: The capital shift shown reflects cumulative reallocation from age {user_age} through age 85.")

        st.subheader("⬇️ Save Your Simulation")
        download_data = {
            "profile": profile,
            "insurance_type": insurance_type,
            "recommendations": st.session_state.get("recs", []),
            "insurance_recommendation": st.session_state.get("insurance_rec", {}),
            "risk_trajectory": st.session_state.get("risk_trajectory", []),
            "family_risk_summary": st.session_state.get("family_risk_summary", {}),
            "high_risk_score": st.session_state.get("high_risk_score", 0),
            "original_cost_df": st.session_state.cost_df.to_dict(orient="list"),
            "updated_cost_df": st.session_state.get("updated_cost_df", pd.DataFrame()).to_dict(orient="list")
        }
        download_json = json.dumps(download_data, indent=2)
        st.download_button(
            label="📥 Download Recommendation Report",
            data=download_json,
            file_name="health_strategy_recommendation.json",
            mime="application/json"
        )