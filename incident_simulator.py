import pandas as pd


def simulate_incident(
    df,
    location,
    incident_type,
    severity
):
    """
    Simulate a traffic incident at a selected location.

    Parameters
    ----------
    df : pandas.DataFrame
        Original traffic dataset.

    location : str
        Location where the incident occurs.

    incident_type : str
        Type of incident.

    severity : int
        Incident severity from 1 to 10.

    Returns
    -------
    pandas.DataFrame
        Modified dataset for simulation.
    """

    simulated_df = df.copy()

    # Find selected location
    selected_index = simulated_df[
        simulated_df["location"] == location
    ].index

    if len(selected_index) == 0:
        raise ValueError(
            f"Location '{location}' not found."
        )

    index = selected_index[0]

    # Make sure severity is within valid range
    severity = max(
        1,
        min(int(severity), 10)
    )

    # --------------------------------------------------------
    # Active incident
    # --------------------------------------------------------
    # current_incidents is designed as 0/1 in the existing
    # risk engine, therefore we set it to 1 rather than
    # increasing it to 2, 3, 4, etc.
    simulated_df.loc[
        index,
        "current_incidents"
    ] = 1

    # --------------------------------------------------------
    # Traffic impact
    # --------------------------------------------------------

    traffic_increase = severity * 3

    simulated_df.loc[
        index,
        "traffic_density"
    ] = min(
        simulated_df.loc[
            index,
            "traffic_density"
        ] + traffic_increase,
        100
    )

    # --------------------------------------------------------
    # Incident-specific impact
    # --------------------------------------------------------

    if incident_type == "Major Accident":

        simulated_df.loc[
            index,
            "road_obstruction"
        ] = min(
            simulated_df.loc[
                index,
                "road_obstruction"
            ] + severity * 4,
            100
        )

        simulated_df.loc[
            index,
            "traffic_violations"
        ] = min(
            simulated_df.loc[
                index,
                "traffic_violations"
            ] + severity,
            100
        )

    elif incident_type == "Minor Accident":

        simulated_df.loc[
            index,
            "road_obstruction"
        ] = min(
            simulated_df.loc[
                index,
                "road_obstruction"
            ] + severity * 2,
            100
        )

    elif incident_type == "Road Blockage":

        simulated_df.loc[
            index,
            "road_obstruction"
        ] = min(
            simulated_df.loc[
                index,
                "road_obstruction"
            ] + severity * 6,
            100
        )

        simulated_df.loc[
            index,
            "traffic_density"
        ] = min(
            simulated_df.loc[
                index,
                "traffic_density"
            ] + severity * 2,
            100
        )

    elif incident_type == "Traffic Jam":

        simulated_df.loc[
            index,
            "traffic_density"
        ] = min(
            simulated_df.loc[
                index,
                "traffic_density"
            ] + severity * 5,
            100
        )

    elif incident_type == "Emergency Vehicle Movement":

        simulated_df.loc[
            index,
            "traffic_density"
        ] = min(
            simulated_df.loc[
                index,
                "traffic_density"
            ] + severity * 2,
            100
        )

    return simulated_df


def get_incident_description(
    incident_type,
    severity
):
    """
    Generate a human-readable explanation
    for the simulated incident.
    """

    descriptions = {

        "Major Accident":
            "A major accident is expected to increase "
            "traffic congestion, road obstruction and "
            "traffic violations.",

        "Minor Accident":
            "A minor accident is expected to cause "
            "moderate congestion and road obstruction.",

        "Road Blockage":
            "A road blockage significantly increases "
            "traffic congestion and obstruction.",

        "Traffic Jam":
            "A traffic jam increases traffic density "
            "and congestion.",

        "Emergency Vehicle Movement":
            "Emergency vehicle movement may temporarily "
            "increase traffic pressure in the area."
    }

    description = descriptions.get(
        incident_type,
        "The incident may increase traffic risk."
    )

    return (
        f"{description} "
        f"Simulation severity: {severity}/10."
    )
