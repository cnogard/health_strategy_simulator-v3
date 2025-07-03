# 🧠 Health Strategy Simulator FAQ

## 📊 GENERAL OVERVIEW

**What is this simulator for?**  
This simulator is part of **Capital Care 360**, a platform built around our vision of a **New Health-First Wealth Paradigm**. It helps shift individuals from reactive health spending to **proactive health investing**, aligning their care decisions with long-term financial goals.

By simulating lifetime healthcare expenses, income, and investment options, the tool empowers you to:
- Optimize your health and financial outcomes
- Build and protect a Capital Care Fund
- Evaluate whether insurance or capital-based care makes more sense
- Prepare for retirement and unforeseen health risks

💡 Ultimately, **Capital Care 360 empowers individuals — not insurance companies — to take control of their health, wealth, and life trajectory.**
---

## ❓ Is Capital Care 360 a new type of insurance company?

**No.**  

**Capital Care 360 is not an insurance company.** It is an **AI-powered financial health agent** that helps individuals and families make smart decisions **today** to secure their healthcare needs **for today and tomorrow**.

Unlike traditional insurance companies — which **pool members to spread risk and optimize cost management over time** — Capital Care 360 focuses on **individual short- and long-term outcomes**. Insurance can protect against catastrophic events, but it often **doesn't guarantee benefits and costs over time** for its members.

**Capital Care 360 complements insurance by:**
- Helping you assess whether you’re **adequately insured today and tomorrow**
- Reallocating **surplus premiums into a capital fund you control**
- Giving you **ownership and flexibility** in managing your care

## 💰 INCOME & EXPENSE LOGIC

**How is monthly income calculated?**  
You enter your take-home monthly income. In family mode, your partner’s income is included too. The simulator also factors in Social Security (~40% of pre-retirement income) and any pension if applicable.

**What counts as expenses?**  
The simulator includes:
- Household expenses (BLS averages or user input)
- Health insurance premiums
- Out-of-pocket costs (adjusted for age, insurance type, and health status)
- Monthly debt payments
- Optional savings contributions

---

## 🧾 INSURANCE & OUT-OF-POCKET (OOP) COSTS

**How are premium and OOP costs estimated?**  
You can either:
- Enter your own premium and OOP values
- Use national benchmarks (adjusted by insurance type and health risk)

All future costs are adjusted for inflation and rising healthcare utilization with age.

**Does my health status affect my costs?**  
Yes. Costs are adjusted using multipliers:
- **Healthy**: Base level
- **Chronic**: 1.25×–1.5×
- **High Risk**: Up to 2×

🧮 **Note on Visual Bumps in Cost Charts**  
Out-of-pocket costs are adjusted using **stepwise correction ratios by age bracket**. For example:
- Ages 35–49 → 1.3×  
- Ages 50–64 → 1.4×  

If your profile crosses into a new age bracket (e.g., from age 44 to 45), your projected OOP costs may jump. This is intentional and based on national cost trends.

---

## 🧬 HEALTH RISK & FAMILY HISTORY

**What if I have chronic illness or a family history?**  
The AI uses both to assess your risk profile:
- **Chronic/High Risk**: Triggers Capital-First plan (Option 1)
- **Healthy + Family History**: Dual strategy (Option 1 + Option 2)
- **Healthy + No Risk**: Insurance optimization likely (Option 2)

Family history doesn’t increase current costs, but it flags future risk for preventive planning.

---

## 🧱 CAPITAL CARE FUND

**What is the Capital Care Fund?**  
The Capital Care Fund is a flexible investment you build to take control of your future healthcare — and your legacy. It has **two core purposes**:

1. **💼 Protection-first**  
   If your healthcare needs rise (due to chronic illness, aging, or unexpected events), the fund becomes your safety net. It helps you cover major expenses **without draining your monthly income or savings**.

2. **🌱 Opportunity-next**  
   If you stay healthy and manage your care efficiently, the fund can become a **legacy asset** — used for family goals, life experiences, or even passed on to the next generation. It grows tax-efficiently and rewards proactive planning.

> **If you need it, it's your bridge to care.  
> If you don't, it's your bridge to freedom.**

**How is fund growth estimated?**  
In the freemium version, we assume:
- Short-term growth rate: ~3% annually
- No withdrawals before retirement

Premium users will get full growth/withdrawal simulation.

---

## 📉 RETIREMENT READINESS & DRAWDOWN

**How do I know if my savings will last?**  
We project your total healthcare costs after retirement and compare them to:
- Your 401(k)
- Savings
- Capital Care Fund
- Pension + Social Security

The retirement readiness chart shows:
- Years when capital is used
- If/when it runs out
- Remaining capital at each age

---

## 🤖 AI RECOMMENDATION LOGIC

**How does the AI pick my plan (Option 1 vs Option 2)?**

| Situation                   | Recommendation                              |
| ---------------------------|---------------------------------------------|
| Chronic or high risk        | Option 1: Build Capital Care Fund           |
| Healthy + family risk       | Option 1 + 2: Build fund + review insurance |
| Healthy + no risk + surplus | Option 2: Optimize insurance                |
| No income or savings        | Health behavior first (not yet eligible)    |

**Can I see how much I’d save by switching plans?**  
Yes. If you're eligible for digital-first care, we show projected savings compared to your current insurance and OOP spend.

---

## 📦 SAVING, UPLOADING & NEXT STEPS

**Can I save or upload my profile later?**  
Yes. You can:
- Save your inputs as a JSON file
- Upload them later to update your plan

**What if my situation changes?**  
You can revisit the simulator to update your income, health status, or goals anytime.


## Is my data secure?
Your data is stored locally unless you choose to share it. Keep backups in secure locations to prevent loss.

---
