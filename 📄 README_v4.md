# Capital Care 360 – Tuku AI Health Strategy Simulator

## 📦 Version: v4.0.0  
**Release Date:** July 3, 2025  
**Status:** ✅ Stable Release

## 🚀 Overview
Capital Care 360 is a dynamic simulator designed to help individuals and families plan for lifetime healthcare costs and optimize financial decisions. Powered by Tuku, your AI health adviser, the platform blends investment logic, care access, and insurance strategy into a single streamlined experience.

## 🧠 Key Features
- Step-by-step simulation of profile, income, care preferences, and investment strategy
- Lifetime healthcare cost projection adjusted for age, risk, and inflation
- Capital Care Fund modeling (short/mid/long-term)
- AI-generated care and financial recommendations
- Pension, 401(k), and Social Security drawdown simulation
- Built-in education via FAQ and visual walkthroughs
- JSON profile upload/download

## 🖥️ How to Run
From terminal:
```bash
streamlit run main.py
```

## 🗂️ Folder Structure
```
/health_strategy_simulator-v4
├── main.py
├── step_1.py ... step_6.py
├── simulator_core.py
├── /modules/
│   ├── chronic_module.py
│   ├── pension_utils.py
│   ├── cost_library.py
│   ├── recommendation_logic.py
├── /assets/
│   ├── Tuku_Analyst.png
│   ├── Tuku_Concerned.png
├── FAQ.md
├── Capital_Care_360_FAQ_FINAL_v4.pdf
├── Health_Strategy_App_Variable_Lexicon.xlsx
```

## 📋 Notes
- Freemium limitations enforced
- No persistent backend — all data is local/session-based
- Designed for beta testing and investor demonstrations

## 🏷️ Git Tag
If using Git:
```bash
git tag -a v4.0.0 -m "Tuku AI Health Strategy Simulator v4.0.0 – Stable Release"
```

---

© 2025 Capital Care 360. All rights reserved.
