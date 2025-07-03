import streamlit as st
from chronic_module import get_chronic_multiplier

def run_step_6(tab7):
    with tab7:
        if not st.session_state.get("step5_submitted") or st.session_state.get("proceed_to_ai", "Not Now") != "Yes":
            st.warning("⚠️ Please complete Step 5 and choose to proceed before continuing.")
            st.stop()

        retirement_gap_start_age = st.session_state.get("retirement_gap_start_age", None)

        st.markdown("## Step 6: Tuku Recommendation")
        # st.image("https://tuku.ai/images/tuku_avatar.png", width=80)  # Replaced with user-provided image below
        st.markdown("*Tuku says:* These insights help you protect your health and finances — let’s review them carefully!")
        st.markdown("**Health Insights:**")
        average_healthcare_pct = st.session_state.get("average_healthcare_pct", None)
        if "locked_average_healthcarei am back. Do you a dragf_pct" not in st.session_state:
            st.session_state["locked_average_healthcare_pct"] = average_healthcare_pct
        # 3. Fix duplicated healthcare cost ratio caused by repeated evaluations
        if "final_average_healthcare_pct" not in st.session_state:
            st.session_state["final_average_healthcare_pct"] = st.session_state.get("locked_average_healthcare_pct", average_healthcare_pct)
        average_healthcare_pct = st.session_state["final_average_healthcare_pct"]
        if average_healthcare_pct is not None:
            if average_healthcare_pct > 8:
                st.markdown(f"- Your average healthcare spending is **{average_healthcare_pct:.1f}%**, which is above the national benchmark of 8%. Consider reviewing your care plan or insurance.")
            elif average_healthcare_pct <= 8:
                st.markdown(f"- Your average healthcare spending is **{average_healthcare_pct:.1f}%**, which is below the national benchmark of 8%. Your current strategy appears efficient, but monitoring trends and preventive steps remains important.")
        else:
            st.markdown("- Healthcare spending ratio not available. Please review Step 5.")

        st.markdown("**Financial Insights:**")
        if retirement_gap_start_age:
            st.markdown(f"- Based on your projections, a retirement funding gap begins at **age {retirement_gap_start_age}**. Explore care optimization and digital-first plans to reduce long-term pressure.")
        else:
            st.markdown("- Your retirement capital is currently on track based on the simulated assumptions.")

        profile = st.session_state.get("profile", {})
        user_age = profile.get("age", st.session_state.get("user_age", 45))
        user_chronic_count = st.session_state.get("user_chronic_count", "None").lower().replace(" ", "_")
        chronic_multiplier = get_chronic_multiplier(user_age, user_chronic_count)
        health_status = profile.get("health_status", "")
        family_history = profile.get("family_history", [])
        insurance_type = profile.get("insurance_type", "")
        available_income = st.session_state.get("available_cash", 0)
        savings_balance = st.session_state.get("savings_start", 0)

        partner_health_status = profile.get("partner_health_status", "")

        # Evaluate health status for Option 2 recommendation eligibility
        option_2_eligible = (
            health_status not in ["chronic", "high_risk"] and
            partner_health_status not in ["chronic", "high_risk"]
        )

        # Insert Tuku callout section immediately after AI insights header, with image and title side by side
        col_tuku, col_text = st.columns([1, 10])
        with col_tuku:
            st.image("Tuku_Concerned.png", width=60)
        with col_text:
            st.markdown("## Tuku’s Recommendations")
        if health_status in ["chronic", "high_risk"]:
            st.markdown("_Tuku says: You’re managing multiple chronic risks — now is the time to safeguard your care pathway with financial protection._")
        else:
            st.markdown("_Tuku says: Prioritize preventive care and consider digital health solutions to optimize your health outcomes and financial stability._")

        # Insert capital_invest_toggle logic before care platform comparisons (per spec)
        capital_invest_toggle = st.radio(
            "Do you want to evaluate how a dedicated Capital Care Investment strategy can help you meet your objectives?",
            ["No", "Yes"],
            key="capital_invest_toggle_radio"
        )

        if capital_invest_toggle == "No":
            st.info("Simulation complete. You can revisit recommendations anytime.")
            st.stop()

        st.markdown("Based on your health risk profile, there are multiple options available to you.")
        if option_2_eligible:
            st.markdown("### 🏥 Health-Driven Capital Care Savings")

            monthly_premium = st.session_state.get("monthly_premium", 0) * chronic_multiplier
            monthly_oop = st.session_state.get("monthly_oop", 0) * chronic_multiplier
            st.markdown(f"**Your estimated monthly premium** (based on Year 1): ${round(monthly_premium):,}")
            st.markdown(f"**Your estimated monthly OOP** (based on Year 1): ${round(monthly_oop):,}")

        if option_2_eligible:
            st.markdown("### 🏥 Care Platform Comparison")

            st.markdown(
                """
                | Provider           | Services Included                                | Est. Monthly Cost     |
                |--------------------|--------------------------------------------------|------------------------|
                | **Mira**           | Urgent care, labs, prescriptions                 | $45–$80               |
                | **One Medical**    | Virtual + in-person care, pediatrics             | $199/year + insurance |
                | **Amazon Clinic**  | 24/7 virtual primary care                        | ~$75                  |
                | **K Health**       | Primary + mental health + urgent care            | $49–$79               |
                | **Teladoc**        | General, mental, dermatology                     | $0–$75 per visit      |
                | **Christus Virtual** | Primary care in Texas/Southeast               | $45                   |
                """
            )

            st.markdown("### 📊 Projected Costs")
            st.markdown("- **Virtual Primary Care Estimate**: $80/mo")
            st.markdown("- **Surgery Bundle Average**: $100/mo")
            st.markdown("- **Vision/Dental Add-On**: $50/mo")
            total_current_spending = monthly_premium + monthly_oop

            total_estimate = 80 + 100 + 50  # Digital-first cost estimate
            delta = total_current_spending - total_estimate

            if monthly_premium == 0 and monthly_oop <= total_estimate:
                st.info("Your current OOP costs are already below digital-first alternatives. However, consider planning ahead as costs may rise due to family risk. Explore upgrade options available to you through our partners' network.")
            elif delta > 5:
                st.success(f"Estimated monthly savings from reallocation: ${delta:.0f}")
            elif -5 <= delta <= 5:
                st.info("Your current spending is roughly equivalent to digital-first alternatives.")
            else:
                st.warning("Digital-first care may not currently offer cost savings based on your current healthcare spending.")
            # --- Insurance Reallocation Trigger (Annual Savings) ---
            if delta > 0:
                annual_savings_option2 = delta * 12
                st.session_state["annual_savings_option2"] = annual_savings_option2
                st.markdown(f"📉 **Estimated Annual Savings from Option 2**: ${annual_savings_option2:,.0f}")

        st.markdown("### 💰 Cash-Driven Capital Care Savings")

        cost_df = st.session_state.cost_df
        current_savings = st.session_state.get("current_savings", st.session_state.get("available_savings_after_retirement", st.session_state.get("savings_start", 0)))
        fund_source = st.session_state.get("capital_fund_source", "Select One")

        # Ensure capital fund sliders are visible and reactive with projected values
        available_cash = st.session_state.get("available_cash", 0)
        st.markdown(f"Available Monthly Income: ${available_cash:,.0f}")
        if available_cash > 0:
            monthly_contribution = st.slider(
                "Monthly amount to contribute from income:",
                0,
                int(available_cash),
                min(100, int(available_cash)),
                key="capital_monthly_contrib"
            )
        else:
            st.info("You have no available cash to contribute this month.")
            monthly_contribution = 0

        st.markdown(f"Available Savings: ${current_savings:,.0f}")
        savings_pct = st.slider("Percentage of savings to allocate to Capital Care Fund:", 0, 100, st.session_state.get("capital_savings_pct", 20), key="capital_savings_pct")
        savings_contribution = current_savings * savings_pct / 100

        annual_contribution = monthly_contribution * 12
        st.session_state["annual_contribution"] = annual_contribution
        initial_capital = savings_contribution + annual_contribution

        st.session_state["capital_fund_source"] = fund_source
        st.session_state["initial_capital"] = initial_capital

        # Healthcare savings component
        healthcare_savings = st.session_state.get("capital_healthcare_savings", 0)
        combined_capital = initial_capital + healthcare_savings
        st.markdown(f"**Projected Capital Care Fund (Year 1): ${combined_capital:,.0f}**")
        st.caption("Note: Projection uses short-term conservative investment growth assumptions. Upgrade for advanced simulation.")

        # Calculate premium savings (redirected from healthcare)
        premium_cost = st.session_state.get("premium_employee_share", 0)
        virtual_care_cost = 80  # Default estimated monthly virtual care cost
        premium_savings = max(0, premium_cost - virtual_care_cost) * 12
        st.session_state["oop_savings"] = premium_savings

        # --- Combined Capital Care Fund Section ---
        st.subheader("📊 Projected Capital Care Fund")
        if health_status in ["chronic", "high_risk"]:
            st.markdown("This projection is based on **personal income and savings** only. Healthcare reallocation is not available at this time.")
        else:
            st.markdown("Includes redirected savings from healthcare + personal income/savings")
        st.info("Note: This projection assumes a short-term investment strategy with an annual growth rate of 3–4%.")

        # Compute projected capital fund using short-term assumptions (freemium version)
        user_age = profile.get("age", st.session_state.get("user_age", 45))
        retirement_age = st.session_state.get("retirement_age", 65)
        years_to_retirement = retirement_age - user_age
        short_term_growth_rate = st.session_state.get("short_term_growth_rate", 0.03)
        cash_contribution = initial_capital
        combined_fund = cash_contribution + premium_savings
        projected_capital_fund = combined_fund * ((1 + short_term_growth_rate) ** years_to_retirement)

        st.markdown(f"**Projected Capital Care Fund at Retirement:** ${projected_capital_fund:,.0f}")
        st.caption("This is a simplified estimate for the freemium version. Actual investment returns and health costs may vary.")

        # --- Graph: Combined Capital Care Fund Over Time ---
        import matplotlib.pyplot as plt
        import numpy as np

        years = np.arange(0, years_to_retirement + 1)
        fund_values = combined_fund * (1 + short_term_growth_rate) ** years

        # --- Graph: Capital Fund vs. Projected Healthcare Costs ---
        projected_healthcare_costs = np.array([
            (st.session_state["projected_oop"][i] if "projected_oop" in st.session_state else 7000 * (1.05 ** i)) * chronic_multiplier
            for i in range(len(years))
        ])
        bar_width = 0.4
        ages = user_age + years
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(ages - bar_width/2, fund_values, width=bar_width, label="Capital Care Fund", color="#2a7cba")
        ax.bar(ages + bar_width/2, projected_healthcare_costs, width=bar_width, label="Annual Healthcare Costs", color="#ba2a2a")
        ax.set_title("Capital Fund vs. Annual Healthcare Costs")
        ax.set_xlabel("Age")
        ax.set_ylabel("Dollars ($)")
        ax.legend()
        ax.grid(alpha=0.3)
        st.pyplot(fig)

        # --- Sliders for monthly_contribution and savings_pct remain above; values dynamically update cash_contribution ---

        st.image("https://tuku.ai/images/tuku_thumbs_up.png", width=60)
        st.markdown("You’re combining healthcare savings and cash reserves to build a stronger foundation for your future health expenses. This strategy gives you flexibility, especially as costs rise in later life.")

        recommendation_text = ""
        drawdown_option = ""

        if health_status in ["chronic", "high_risk"]:
            if available_income > 0 and savings_balance > 0:
                recommendation_text = "🧱 **Recommendation:** You are at risk and already in a treatment window. Focus on building a **Capital Care Fund** using available savings or income. (Option 1)"
                drawdown_option = "Option 1"
            elif savings_balance > 0:
                recommendation_text = "💰 **Recommendation:** Use existing savings to begin a **Capital Care Fund**. (Option 1)"
                drawdown_option = "Option 1"
            elif available_income > 0:
                recommendation_text = "💡 **Recommendation:** Contribute from income to a **Capital Care Fund** for future treatment needs. (Option 1)"
                drawdown_option = "Option 1"
            else:
                st.image("https://tuku.ai/images/tuku_encourage.png", width=60)
                st.markdown("You may not yet be ready for financial care strategies. Instead, start your **health readiness journey** with small lifestyle changes — like improving diet, sleep, movement, and stress management. These steps will help you qualify for financial options in the future.\n\n_Consider exploring resources from patient advocacy groups, digital wellness platforms, or community support services._")
                drawdown_option = ""
        else:
            if family_history:
                if available_income > 0:
                    recommendation_text = "🔁 **Recommendation:** You’re healthy with family risk. Begin **Capital + Insurance Optimization** (**Option 1 + 2**)."
                    drawdown_option = "Option 1 + Option 2"
                else:
                    recommendation_text = "📉 **Recommendation:** Healthy with family risk. Consider **insurance review** (**Option 2**)."
                    drawdown_option = "Option 2"
            else:
                if available_income > 0:
                    recommendation_text = "✅ **Recommendation:** Ideal profile for a **Capital Health Fund** (**Option 1 + 2**)."
                    drawdown_option = "Option 1 + Option 2"
                else:
                    recommendation_text = "🛡️ **Recommendation:** Overinsured. Start with **Option 2** and allocate surplus later."
                    drawdown_option = "Option 2"


        st.success("This concludes the AI-guided retirement and care funding recommendation.")

        # --- Capital Longevity Insight from Retirement Readiness ---
        capital_remaining = st.session_state.get("capital_remaining_over_time", [])
        chart_ages = st.session_state.get("retirement_chart_ages", [])
        # Smart Highlight: Capital Longevity (Years Covered)
        if capital_remaining and chart_ages:
            years_covered = len([val for val in capital_remaining if val > 0])
            st.info(f"📊 Your Capital Care Fund is projected to support your healthcare needs for approximately **{years_covered} years** into retirement.")
        else:
            depletion_age = None
            for age, cap in zip(chart_ages, capital_remaining):
                if cap <= 0:
                    depletion_age = age
                    break
            if depletion_age:
                st.warning(f"⚠️ Your projected capital will be depleted by age **{depletion_age}**. Consider increasing savings or optimizing healthcare strategy.")
            elif capital_remaining:
                st.success(f"✅ Your capital resources are projected to cover retirement expenses through at least age **{chart_ages[-1]}**.")
        # --- Final Insight Block: How This Strategy Supports Your Goals ---
        st.subheader("📈 How This Strategy Supports Your Goals")
        st.markdown("You're combining redirected healthcare savings, personal income, and existing savings to build a Capital Care Fund.")
        if drawdown_option:
            st.markdown(f"This fund supports your selected strategy — **{drawdown_option}** — and protects against rising health costs in retirement.")
        else:
            st.markdown("This fund enhances your ability to cover future health costs as your needs evolve.")

        st.subheader("🔓 Unlock More Insights")
        upgrade_choice = st.radio("Ready to plan with advanced AI guidance and multi-scenario comparison?", ["Not now", "Upgrade"])
        st.session_state["upgrade_choice"] = upgrade_choice

        # --- Download Plan Option ---
        st.markdown("---")
        st.subheader("📁 Manage Your Plan")
        download_option = st.radio("Would you like to download your health plan?", ["Download My Plan", "Skip for Now"], key="download_plan_step6")

        if download_option == "Download My Plan":
            import json
            export_data = {
                "profile": st.session_state.get("profile", {}),
                "insurance": {
                    "type": st.session_state.get("insurance_type"),
                    "premium": st.session_state.get("premium_cost"),
                    "oop": st.session_state.get("oop_first_year")
                },
                "financials": {
                    "monthly_income": st.session_state.get("monthly_income"),
                    "monthly_expenses": st.session_state.get("monthly_expenses"),
                    "savings_balance": st.session_state.get("savings_balance"),
                    "debt_monthly": st.session_state.get("debt_monthly_payment")
                },
                "capital_strategy": {
                    "short_term": st.session_state.get("short_term_allocation"),
                    "mid_term": st.session_state.get("mid_term_allocation"),
                    "long_term": st.session_state.get("long_term_allocation")
                },
                "retirement": {
                    "pension_user": st.session_state.get("pension_user"),
                    "pension_partner": st.session_state.get("pension_partner")
                }
            }
            download_str = json.dumps(export_data, indent=2)
            st.download_button("📥 Download Your Plan", data=download_str, file_name="my_health_plan.json", mime="application/json", key="download_button_step6")

        # --- Reset/Restart Plan Option ---
        st.markdown("---")
        if st.button("🔄 Restart Plan", key="reset_button_step1"):
            for key in list(st.session_state.keys()):
                if key not in ["user_authenticated", "default_user_id"]:
                    del st.session_state[key]
            st.experimental_rerun()