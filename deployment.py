import pandas as pd


def calculate_priority_score(row):
    """
    Calculate AI deployment priority dynamically.

    Active incidents receive a strong priority boost.
    CRITICAL incidents are always treated as urgent.
    """

    risk_score = float(
        row.get("risk_score", 0)
    )

    risk_level = str(
        row.get("risk_level", "MODERATE")
    ).upper()

    officers = int(
        row.get("police_officers", 0)
    )

    incidents = int(
        row.get("current_incidents", 0)
    )

    # ========================================================
    # POLICE COVERAGE GAP
    # ========================================================

    if officers <= 0:
        coverage_gap = 100

    elif officers == 1:
        coverage_gap = 70

    elif officers == 2:
        coverage_gap = 40

    else:
        coverage_gap = 20


    # ========================================================
    # INCIDENT URGENCY
    # ========================================================

    if incidents > 0:
        incident_priority = 100
    else:
        incident_priority = 0


    # ========================================================
    # RISK LEVEL BOOST
    # ========================================================

    if risk_level == "CRITICAL":
        risk_level_boost = 30

    elif risk_level == "HIGH":
        risk_level_boost = 10

    elif risk_level == "MODERATE":
        risk_level_boost = 0

    else:
        risk_level_boost = 0


    # ========================================================
    # AI PRIORITY SCORE
    # ========================================================
    #
    # Active incidents are intentionally given strong weight.
    # This prevents an old high-risk location from permanently
    # beating a newly simulated critical incident.
    #

    priority = (
        risk_score * 0.50
        + coverage_gap * 0.15
        + incident_priority * 0.25
        + risk_level_boost * 0.10
    )

    return round(
        min(priority, 100),
        2
    )


def calculate_deployment_needs(df):
    """
    Calculate deployment priority for the CURRENT traffic state.
    """

    result = df.copy()

    result["priority_score"] = result.apply(
        calculate_priority_score,
        axis=1
    )

    result = result.sort_values(
        "priority_score",
        ascending=False
    ).reset_index(drop=True)

    return result


def recommend_deployment(
    df,
    available_officers
):
    """
    Recommend police deployment based on the CURRENT
    traffic risk and incident state.
    """

    result = calculate_deployment_needs(df)

    result["recommended_officers"] = 0

    remaining = int(
        available_officers
    )

    # ========================================================
    # DEPLOY IN PRIORITY ORDER
    # ========================================================

    for index in result.index:

        if remaining <= 0:
            break

        risk = float(
            result.loc[
                index,
                "risk_score"
            ]
        )

        risk_level = str(
            result.loc[
                index,
                "risk_level"
            ]
        ).upper()

        incidents = int(
            result.loc[
                index,
                "current_incidents"
            ]
        )

        # ====================================================
        # BASE DEPLOYMENT
        # ====================================================

        if risk_level == "CRITICAL" or risk >= 80:

            required = 3

        elif risk_level == "HIGH" or risk >= 65:

            required = 2

        elif risk_level == "MODERATE" or risk >= 45:

            required = 1

        else:

            required = 0


        # ====================================================
        # ACTIVE INCIDENT OVERRIDE
        # ====================================================

        if incidents > 0:

            if risk_level == "CRITICAL":

                required = max(
                    required,
                    3
                )

            elif risk_level == "HIGH":

                required = max(
                    required,
                    2
                )

            else:

                required = max(
                    required,
                    1
                )


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
