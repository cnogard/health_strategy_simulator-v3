


def get_true_lifetime_healthcare_cost(risk_factors, gender=None):
    """
    Estimates the total true lifetime healthcare cost for an uninsured individual,
    based on cardiovascular and lifestyle risk factors. Based on data from PMC10314135.
    Race is excluded for freemium version.

    Parameters:
        risk_factors (list): A list of strings indicating risk factors present.
            Accepted values: 'diabetes', 'obesity', 'smoking', 'hypertension'
        gender (str, optional): 'Male' or 'Female'

    Returns:
        float: Estimated lifetime cost in USD
    """
    base_cost = 75200  # Healthy, no risk factor baseline

    # Risk factor adjustments
    if 'diabetes' in risk_factors:
        base_cost += 28075
    if 'obesity' in risk_factors:
        base_cost += 8816
    if 'smoking' in risk_factors:
        base_cost += 3980
    if 'hypertension' in risk_factors:
        base_cost += 528

    # Gender adjustment
    if gender and gender.lower() == 'male':
        base_cost += 5987

    return base_cost