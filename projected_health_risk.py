# projected_health_risk.py

def get_risk_insight(age, health_status):
    # Returns a simple qualitative insight
    if health_status == "high":
        return "Your current health status suggests elevated long-term risk."
    elif health_status == "chronic":
        return "You are managing a chronic condition. Monitor regularly and plan proactively."
    else:
        return "You are currently low-risk. Maintain preventive care."

def get_risk_trajectory(age, health_status):
    # Returns a risk trajectory list based on age and health status
    years = list(range(age, 86))
    trajectory = []

    # Define starting risk and slope per status
    if health_status == "high_risk":
        base_risk = 0.5 if age < 18 else 0.6
        slope = 0.025
    elif health_status == "chronic":
        trajectory = [0.75] * len(years)
        return trajectory
    else:  # healthy
        base_risk = 0.1 if age < 18 else 0.2
        slope = 0.01

    # Generate trajectory with capping at 1.0
    for i in range(len(years)):
        risk = min(1.0, base_risk + slope * i)
        trajectory.append(risk)

    return trajectory