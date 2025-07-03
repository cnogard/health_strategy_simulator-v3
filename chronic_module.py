# chronic_module.py

# Chronic prevalence and multiplier logic
CHRONIC_PREVALENCE = {
    "under_60": {
        "one_or_more": 0.60,
        "two_or_more": 0.40
    },
    "60_and_over": {
        "one_or_more": 0.95,
        "two_or_more": 0.79
    }
}

def get_chronic_multiplier(age, num_conditions):
    if age < 60:
        if num_conditions == 0:
            return 1.0
        elif num_conditions == 1:
            return 1.15
        else:
            return 1.3
    else:
        if num_conditions == 0:
            return 1.0
        elif num_conditions == 1:
            return 1.3
        else:
            return 1.5