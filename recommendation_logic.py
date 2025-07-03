

import streamlit as st

def recommend_option_1_only(profile, income, savings):
    return f"""
    🐢 Tuku says: Based on your profile, a dedicated Capital Care Fund is the most effective strategy.

    You can start by allocating a portion of your savings and monthly income toward long-term care planning.
    
    **Available Monthly Income:** ${income:,.0f}  
    **Available Savings:** ${savings:,.0f}

    Consider starting small and growing your contributions over time.
    """, "option_1_only"


def recommend_option_1_plus_2(profile, income, insurance_type):
    return f"""
    🐢 Tuku says: You may benefit from both a capital care fund and smarter insurance choices.

    Your current plan may be more expensive than needed. Explore lower-premium options and redirect the savings toward long-term care funding.

    We'll help you compare your current plan vs. digital-first or bundled care platforms.
    """, "option_1_plus_2"


def recommend_lifestyle_guidance(profile):
    return """
    🐢 Tuku says: You may not have enough free cash or savings for a capital care strategy right now.

    Let’s focus on what you can control:  
    - Prioritize preventive care  
    - Build healthy habits (sleep, nutrition, exercise)  
    - Explore local or low-cost digital health support

    Every step improves your future options.
    """, "lifestyle_guidance"