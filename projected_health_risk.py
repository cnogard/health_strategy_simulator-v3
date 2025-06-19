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
    # Returns a fake risk trajectory list between 0 and 1
    years = list(range(age, 86))
    if health_status == "high":
        return [min(1.0, 0.6 + 0.02 * i) for i in range(len(years))]
    elif health_status == "chronic":
        return [min(1.0, 0.4 + 0.015 * i) for i in range(len(years))]
    else:
        return [min(1.0, 0.2 + 0.01 * i) for i in range(len(years))]