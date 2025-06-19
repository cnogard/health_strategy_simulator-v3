import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def show_high_risk_capsule(age, trajectory, cost_df):

    print("🚨 High-Risk Health Trajectory Identified")
    print("Your projected risk exceeds safe thresholds in future years. Consider taking action now to prepare.")

    # Show chart of risk trajectory
    age_range = cost_df["Age"][:len(trajectory)]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(age_range, trajectory, label="Risk Score", color="black", linewidth=2)
    ax.fill_between(age_range, 0, trajectory, where=[r < 0.9 for r in trajectory], color="orange", alpha=0.3)
    ax.fill_between(age_range, 0, trajectory, where=[r >= 0.9 for r in trajectory], color="red", alpha=0.4)
    ax.set_xlabel("Age")
    ax.set_ylabel("Risk Score")
    ax.set_title("Projected High Risk Timeline")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.show()

    # Show financial stress signal
    years_to_risk = next((i for i, r in enumerate(trajectory) if r >= 0.9), None)
    if years_to_risk is not None:
        age_critical = age + years_to_risk
        print(f"⚠️ Your risk is projected to become critical at age {age_critical}. Consider rebalancing savings or insurance.")

    # Optional advice
    print("💡 Proactive Suggestions:")
    print("- Set aside emergency health fund.")
    print("- Consider catastrophic insurance options.")
    print("- Prioritize preventive care and screenings.")


def compute_high_risk_score(profile):
    from projected_health_risk import get_risk_insight, get_risk_trajectory

    trajectory = get_risk_trajectory(profile["age"], profile["health_status"])

    # Clean and convert trajectory to float
    cleaned_trajectory = []
    for r in trajectory:
        try:
            cleaned_trajectory.append(float(r))
        except (ValueError, TypeError):
            continue  # Skip any non-numeric values

    high_risk_years = sum(1 for r in cleaned_trajectory if r >= 0.9)
    return high_risk_years / len(cleaned_trajectory) if cleaned_trajectory else 0
