import pandas as pd


def calculate_priority_score(row):
    """
    Calculate deployment priority for a location.

    Higher score = greater need for police deployment.
    """

    risk_score = row["risk_score"]

    # More officers already present = lower deployment need
    officers = row["police_officers"]

    if officers == 0:
        coverage_gap = 100
    elif officers == 1:
        coverage_gap = 70
    elif officers == 2:
        coverage_gap = 40
    else:
        coverage_gap = 20

    # Current incident increases urgency
    incident_priority = row["current_incidents"] * 100

    priority = (
        risk_score * 0.60
        + coverage_gap * 0.25
        + incident_priority * 0.15
    )

    return round(min(priority, 100), 2)


def calculate_deployment_needs(df):
    """
    Calculate deployment priority for every location.
    """

    result = df.copy()

    result["priority_score"] = result.apply(
        calculate_priority_score,
        axis=1
    )

    result = result.sort_values(
        "priority_score",
        ascending=False
    )

    return result


def recommend_deployment(df, available_officers):
    """
    Recommend deployment of limited police officers.

    Higher-priority locations receive officers first.
    """

    result = calculate_deployment_needs(df)

    result["recommended_officers"] = 0

    remaining = available_officers

    # Allocate officers according to priority
    for index in result.index:

        if remaining <= 0:
            break

        risk = result.loc[index, "risk_score"]

        if risk >= 80:
            required = 3
        elif risk >= 65:
            required = 2
        elif risk >= 45:
            required = 1
        else:
            required = 0

        allocation = min(
            required,
            remaining
        )

        result.loc[
            index,
            "recommended_officers"
        ] = allocation

        remaining -= allocation

    return result
