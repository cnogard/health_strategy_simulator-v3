import streamlit as st

from step_1 import run_step_1
from step_2 import run_step_2
from step_3 import run_step_3
from step_4 import run_step_4
from step_5 import run_step_5
from step_6 import run_step_6


st.set_page_config(layout="wide", page_title="Health Strategy Simulator")

# Access control
with st.sidebar:
    st.header("🔐 Beta Access")
    code = st.text_input("Enter beta access code:", type="password")
    if code != "HSS_Beta_2025v4!":
        st.stop()

import os

logo_path = "logo_capitalcare360.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=200)
else:
    st.warning("Logo image not found.")
tabs = st.tabs([
    "Welcome",
    "Step 1: Profile & Insurance",
    "Step 2: Financial Inputs",
    "Step 3: Health Risk Outlook",
    "Step 4: Capital Simulation",
    "Step 5: Summary Dashboard",
    "Step 6: Tuku Recommendation",
    "FAQ"
])

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab_faq = tabs
with tab_faq:
    st.subheader("📘 Capital Care 360 FAQ")
    st.markdown("Here are the most frequently asked questions about the simulator and how it works.")

with tab0:
    st.image("Tuku_Default_Health_Adviser.png", width=80)
    st.title("Welcome to Tuku, Your Health & Financial Strategy Simulator")

    st.markdown("""
    ## 📉 U.S. Population Trends Matter More Than You Think

    The U.S. birth rate has been **steadily declining**, reshaping how healthcare is funded and delivered:
    - 👶 **Birth rate in 2023**: 54.4 births per 1,000 women — a historic low (CDC)
    - 👵 **By 2034**, adults 65+ will outnumber children under 18
    - 🧓 The **aging population means fewer workers** funding more retiree care  
    This demographic shift affects **how much you’ll pay** and **what care you can expect** in the future.
    ---
    ## 💸 How U.S. Healthcare Is Funded

    | Funding Source         | Who Pays                | % of Total Spend | Notes |
    |------------------------|-------------------------|------------------|-------|
    | Employer Insurance     | Employers + Employees   | ~47%             | Common for working adults |
    | Medicaid               | Government (State/Fed)  | ~17%             | For low-income households |
    | Medicare               | Federal Government      | ~14%             | For adults 65+ |
    | Out-of-Pocket (OOP)    | You                     | ~11%             | Fastest-growing burden |
    | Other Programs         | Gov’t & Private         | ~11%             | CHIP, VA, subsidies |

    📈 **Healthcare inflation** and **longer lifespans** mean that *even healthy individuals* should plan ahead.

    ---
    ## 🚀 Why This Simulator Exists

    Most tools only look at **expenses or benefits** — this simulator shows the full picture:
    - Health risks + insurance decisions + income = 🔍 smarter strategies  
    - See how your plan holds up over time  
    - Build a **capital care fund** to cover what insurance won’t  
    - Get AI-powered tips from 🐢 **Tuku**, your Health Adviser

    ### 🧠 Who is Tuku?
    Meet Tuku, your health adviser. Tuku is a wise turtle who helps you understand risk, stay calm, and plan confidently.   
    """)

    tuku_image_path = "Tuku_Happy.png"
    if os.path.exists(tuku_image_path):
        st.image(tuku_image_path, width=60)

    st.markdown("""
    Look out for **Tuku’s insights** in every step! It will help you budget for your healthcare expenses by integrating your health profile, insurance choices, income, and savings.  

    Unlike traditional tools, Tuku will show you how your **financial and health decisions impact each other over time** — and how investing in your well-being can build long-term wealth.

    ---
    Tuku will help you **see the blind spots** in both your financial and care strategies — and empower you to make smarter, more personalized decisions.

    ---
    ### 🧩 What You'll Be Able to Do with Tuku
    - Understand how your **health risk** affects insurance costs and care needs  
    - Compare **traditional insurance** vs. **capital-based care strategies**  
    - See how much you need to save to **avoid future gaps** in healthcare funding  
    - Explore **care alternatives** (like digital-first plans and surgery bundles)  
    - Get **AI-powered recommendations** tailored to your profile

    ---
    ### 🛠️ How Tuku Works
    Tuku will walk you through 6 steps:
    1. **Profile Setup** – Age, health, family, and insurance info  
    2. **Financial Snapshot** – Income, expenses, debt, and savings  
    3. **Health Risk Outlook** – Lifetime cost projections based on your profile  
    4. **Capital Strategy** – See how savings and investments can offset medical costs  
    5. **Summary Dashboard** – Check retirement readiness and cost breakdowns  
    6. **Tuku’s Recommendations** – Smart suggestions to optimize your plan

    ---
    👉 **Let’s begin. Use the sidebar or the steps above to start your simulation.**
    """)

    st.markdown("---")
    st.subheader("📁 Manage Your Plan")
    upload_download_action = st.radio("Would you like to upload or download your health plan?", ["Download My Plan", "Upload a Saved Plan", "Skip for Now"], key="upload_download_radio")

    import json

    if upload_download_action == "Download My Plan":
        plan_data = {
            "profile": {
                "age": st.session_state.get("age"),
                "gender": st.session_state.get("gender"),
                "health_status": st.session_state.get("health_status"),
                "family_status": st.session_state.get("family_status"),
                "family_history": st.session_state.get("family_history")
            },
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
        json_str = json.dumps(plan_data, indent=2)
        st.download_button("📥 Download Your Plan", data=json_str, file_name="my_health_plan.json", mime="application/json")

    elif upload_download_action == "Upload a Saved Plan":
        uploaded_file = st.file_uploader("📥 Upload your saved health plan (.json)", type="json")
        if uploaded_file:
            imported_data = json.load(uploaded_file)
            try:
                st.session_state.update({
                    "age": imported_data["profile"].get("age"),
                    "gender": imported_data["profile"].get("gender"),
                    "health_status": imported_data["profile"].get("health_status"),
                    "family_status": imported_data["profile"].get("family_status"),
                    "family_history": imported_data["profile"].get("family_history"),
                    "insurance_type": imported_data["insurance"].get("type"),
                    "premium_cost": imported_data["insurance"].get("premium"),
                    "oop_first_year": imported_data["insurance"].get("oop"),
                    "monthly_income": imported_data["financials"].get("monthly_income"),
                    "monthly_expenses": imported_data["financials"].get("monthly_expenses"),
                    "savings_balance": imported_data["financials"].get("savings_balance"),
                    "debt_monthly_payment": imported_data["financials"].get("debt_monthly"),
                    "short_term_allocation": imported_data["capital_strategy"].get("short_term"),
                    "mid_term_allocation": imported_data["capital_strategy"].get("mid_term"),
                    "long_term_allocation": imported_data["capital_strategy"].get("long_term"),
                    "pension_user": imported_data["retirement"].get("pension_user"),
                    "pension_partner": imported_data["retirement"].get("pension_partner")
                })
                st.success("✅ Your plan was successfully imported!")
            except Exception as e:
                st.error(f"⚠️ Import failed: {e}")

    st.success("Ready? Use the sidebar or click above to start Step 1.")

faq_path = "faq.md"
if os.path.exists(faq_path):
    with open(faq_path, "r") as f:
        st.markdown(f.read())
else:
    st.warning("FAQ file not found.")

with tab1:
    run_step_1(tab1)

with tab2:
    run_step_2(tab2)

with tab3:
    run_step_3(tab3)

with tab4:
    run_step_4(tab4)

with tab5:
    run_step_5(tab5)

with tab6:
    run_step_6(tab6)
