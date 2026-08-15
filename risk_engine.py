import pandas as pd


def calculate_risk_score(row):
    """
    Calculate traffic risk score from 0 to 100.
    """

    traffic = row["traffic_density"]
    accidents = row["accident_history"]
    violations = row["traffic_violations"]

    # Convert current incident (0/1) into a 0-100 risk contribution
    incident = row["current_incidents"] * 100

    obstruction = row["road_obstruction"]
    weather = row["weather_risk"]
    peak = row["peak_activity"]

    # Police coverage gap
    # More officers = lower risk
    officers = row["police_officers"]

    if officers == 0:
        police_gap = 100
    elif officers == 1:
        police_gap = 70
    elif officers == 2:
        police_gap = 40
    else:
        police_gap = 20

    # Weighted risk score
    score = (
        traffic * 0.25 +
        accidents * 0.20 +
        violations * 0.15 +
        incident * 0.15 +
        police_gap * 0.10 +
        obstruction * 0.05 +
        weather * 0.05 +
        peak * 0.05
    )

    return round(min(score, 100), 2)


def classify_risk(score):
    """
    Convert numerical risk score into a risk category.
    """

    if score >= 80:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 45:
        return "MODERATE"
    else:
        return "LOW"


def add_risk_analysis(df):
    """
    Add risk score and risk level to the dataset.
    """

    df = df.copy()

    df["risk_score"] = df.apply(
        calculate_risk_score,
        axis=1
    )

    df["risk_level"] = df["risk_score"].apply(
        classify_risk
    )

    return df


def explain_risk(row):
    """
    Explain why a location has a high risk.
    """

    reasons = []

    if row["traffic_density"] >= 80:
        reasons.append("High traffic density")

    if row["accident_history"] >= 70:
        reasons.append("High accident history")

    if row["traffic_violations"] >= 75:
        reasons.append("High traffic violations")

    if row["current_incidents"] > 0:
        reasons.append("Active incident")

    if row["police_officers"] <= 1:
        reasons.append("Insufficient police coverage")

    if row["road_obstruction"] >= 30:
        reasons.append("Road obstruction")

    if row["weather_risk"] >= 20:
        reasons.append("Weather risk")

    if row["peak_activity"] >= 85:
        reasons.append("Peak traffic activity")

    if not reasons:
        reasons.append("Normal traffic conditions")

    return reasons
