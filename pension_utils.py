# pension_utils.py

# Default annual pension income estimates (used if user/partner doesn't know amount)
DEFAULT_PENSION_VALUES = {
    "none": 0,
    "private": 11040,     # Median private pension
    "state": 24980,       # Median state/local pension
    "federal": 26380      # Median federal pension
}

PENSION_STATS_SOURCES = {
    "pension_rights_center": "https://pensionrights.org/resource/income-from-pensions/?utm_source=chatgpt.com",
    "wikipedia_retirement": "https://en.wikipedia.org/wiki/Retirement?utm_source=chatgpt.com"
}