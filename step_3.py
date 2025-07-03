import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
# from health_risk_module import get_risk_trajectory  # Ensure this is accessible
from chronic_module import get_chronic_multiplier

# --- Risk trajectory function ---
def get_risk_trajectory(age, health_status):
    base_curve = {
        "healthy": [0.2 + 0.005 * i for i in range(50)],
        "chronic": [0.4 + 0.0075 * i for i in range(50)],
        "high_risk": [0.5 + 0.01 * i for i in range(50)]
    }
    traj = base_curve.get(health_status.lower(), base_curve["healthy"])
    return traj[:50]

def run_step_3(tab4):
    with tab4:
        st.header("Step 3: Health Risk Outlook")

        profile = st.session_state.get("profile", {})
        cost_df = st.session_state.get("cost_df", pd.DataFrame())
        user_age = profile.get("age", 40)
        user_chronic_count = st.session_state.get("user_chronic_count", "None").lower().replace(" ", "_")
        chronic_multiplier = get_chronic_multiplier(user_age, user_chronic_count)
        st.session_state["chronic_multiplier"] = chronic_multiplier
        health_status = profile.get("health_status", "healthy")
        family_history = profile.get("family_history", [])
        dependent_ages = st.session_state.get("dependent_ages", [])
        dependent_health_statuses = st.session_state.get("dependent_health_statuses", [])

        user_traj = get_risk_trajectory(user_age, health_status)
        risk_trajectory = user_traj
        st.session_state["risk_trajectory"] = risk_trajectory

        risk_values = [user_traj[0]]
        individual_ratios = [("User", user_age, health_status, user_traj[0])]

        partner_age = profile.get("partner_age")
        partner_health_status = profile.get("partner_health_status")
        if partner_age is not None and partner_health_status is not None:
            partner_chronic_count = st.session_state.get("partner_chronic_count", "None").lower().replace(" ", "_")
            partner_multiplier = get_chronic_multiplier(partner_age, partner_chronic_count)
            st.session_state["partner_chronic_multiplier"] = partner_multiplier
            partner_traj = get_risk_trajectory(partner_age, partner_health_status)
            risk_values.append(partner_traj[0])
            individual_ratios.append(("Partner", partner_age, partner_health_status, partner_traj[0]))

        for i, (dep_age, dep_status) in enumerate(zip(dependent_ages, dependent_health_statuses)):
            dep_traj = get_risk_trajectory(dep_age, dep_status)
            risk_values.append(dep_traj[0])
            individual_ratios.append((f"Dependent #{i+1}", dep_age, dep_status, dep_traj[0]))

        def compute_health_risk_ratio(profile):
            def get_individual_risk(health_status, family_history):
                base_risk = {"healthy": 0.20, "chronic": 0.40, "high_risk": 0.50}.get(health_status, 0.20)
                if family_history:
                    base_risk += 0.10
                return min(base_risk, 1.0)

            user_risk = get_individual_risk(profile.get("health_status", "healthy"), bool(profile.get("family_history", [])))
            partner_risk = 0
            dep_risks = []
            if profile.get("family_status") == "family":
                partner_risk = get_individual_risk(profile.get("partner_health_status", "healthy"), bool(profile.get("partner_family_history", [])))
                for dep in profile.get("dependents", []):
                    dep_risks.append(get_individual_risk(dep.get("health_status", "healthy"), False))

            score = 0.5 * user_risk + 0.3 * partner_risk
            if dep_risks:
                dep_weight = 0.2 / len(dep_risks)
                score += sum(dep_weight * r for r in dep_risks)
            return round(min(score, 1.0), 2)

        # Lifetime average
        family_trajectories = []
        for label, age, status, _ in individual_ratios:
            traj = get_risk_trajectory(age, status)
            family_trajectories.append((label, age, status, traj))

        total_weight = 0
        weighted_lifetime_sum = 0
        for label, age, status, traj in family_trajectories:
            weight = 1.0 if label == "User" else 0.9 if label == "Partner" else (0.3 if age <= 6 else 0.4 if age <= 12 else 0.5)
            weighted_lifetime_sum += sum(traj) / len(traj) * weight
            total_weight += weight

        weighted_avg_lifetime_risk = weighted_lifetime_sum / total_weight if total_weight > 0 else 0
        st.session_state["lifetime_health_risk_ratio"] = weighted_avg_lifetime_risk

        avg_health_risk_ratio = compute_health_risk_ratio(profile)
        st.subheader("🩺 Health Risk Ratio")

        # Updated: Side-by-side pie charts for Health Risk Ratios (Health Risk vs Remaining)
        labels = ["Health Risk", ""]
        colors = ["#FF9999", "#DDDDDD"]
        sizes1 = [risk_values[0], 1 - risk_values[0]]
        sizes2 = [weighted_avg_lifetime_risk, 1 - weighted_avg_lifetime_risk]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        ax1.pie(
            sizes1,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f"{pct:.0f}%" if pct == round(sizes1[0]*100) else "",
            startangle=90
        )
        ax1.axis("equal")
        ax1.set_title("Year 1 Health Risk", fontsize=14, fontweight="bold")

        ax2.pie(
            sizes2,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f"{pct:.0f}%" if pct > 0 and pct < 100 and pct > 50 else "",
            startangle=90
        )
        ax2.axis("equal")
        ax2.set_title("Lifetime Average Risk", fontsize=14, fontweight="bold")

        st.pyplot(fig)

        tuku_image_path = "Tuku_Default_Health_Adviser.png"
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image(tuku_image_path, width=60)
        with col2:
            st.markdown("**Tuku’s Observation**: Your current health risk level is {:.0f}%. If your profile stays unchanged, your projected lifetime health risk remains around {:.0f}%. This suggests that your long-term care needs are {}. Consider preventive care and lifestyle choices to lower your future burden.".format(
                risk_values[0]*100,
                weighted_avg_lifetime_risk*100,
                "manageable" if weighted_avg_lifetime_risk < 0.4 else "significant"
            ))

        st.markdown("This represents your family's projected average health burden over time.")

        # Cost Projections
        base_premium = st.session_state.get("base_premium", 6000)
        base_oop = st.session_state.get("base_oop", 3000)
        inflation = st.session_state.get("inflation_rate", 0.03)
        base_premium *= chronic_multiplier
        base_oop *= chronic_multiplier
        years = len(cost_df)
        premiums = [base_premium * ((1 + inflation) ** i) for i in range(years)]
        oop = [base_oop * ((1 + inflation) ** i) for i in range(years)]
        st.session_state["premiums"] = premiums
        st.session_state["oop"] = oop
        st.session_state["healthcare"] = [premiums[i] + oop[i] for i in range(years)]
        # Ensure correct age alignment for downstream steps
        st.session_state["ages"] = list(range(user_age, user_age + years))

        st.subheader("📈 Healthcare Cost Projection")
        total_cost = sum(premiums) + sum(oop)
        st.markdown(f"💰 **Estimated Lifetime Healthcare Cost**: ${total_cost:,.0f}")
        if not cost_df.empty:
            st.line_chart(cost_df.set_index("Age")[["OOP Cost", "Premiums"]])

        st.subheader("🔍 Potential Health Blind Spots")
        blind_spot_messages = []
        if health_status == "high_risk":
            blind_spot_messages.append("🚨 You are in a high-risk health category...")
        elif health_status == "chronic":
            blind_spot_messages.append("⚠️ You are managing a chronic condition...")
        elif health_status == "healthy":
            blind_spot_messages.append("✅ You are currently healthy.")

        if profile.get("family_history"):
            blind_spot_messages.append("🧬 Your family history includes high-risk conditions...")

        if profile.get("partner_health_status", "") in ["chronic", "high_risk"]:
            blind_spot_messages.append("💑 Your partner has a health condition...")
        if any(status in ["chronic", "high_risk"] for status in dependent_health_statuses):
            blind_spot_messages.append("👶 One or more of your dependents have chronic or high-risk conditions...")

        # TODO: Expand this section with multiple answer variants using different Tuku moods (e.g., concerned, positive, cautious) based on user health status and family risk.

        if blind_spot_messages:
            for msg in blind_spot_messages:
                st.markdown(f"- {msg}")
        else:
            st.success("✅ No health blind spots detected.")

        st.session_state.step3_submitted = True