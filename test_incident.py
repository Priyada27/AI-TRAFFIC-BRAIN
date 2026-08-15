import pandas as pd

from incident_simulator import simulate_incident
from risk_engine import add_risk_analysis


df = pd.read_csv(
    "data/nagpur_traffic.csv"
)

location = "Medical Square"

before = add_risk_analysis(
    df.copy()
)

before_row = before[
    before["location"] == location
].iloc[0]


print("\n========== BEFORE INCIDENT ==========")

print(
    "Location:",
    location
)

print(
    "Risk Score:",
    before_row["risk_score"]
)

print(
    "Risk Level:",
    before_row["risk_level"]
)

print(
    "Traffic Density:",
    before_row["traffic_density"]
)

print(
    "Current Incident:",
    before_row["current_incidents"]
)


simulated = simulate_incident(
    df,
    location,
    "Major Accident",
    7
)

after = add_risk_analysis(
    simulated
)

after_row = after[
    after["location"] == location
].iloc[0]


print("\n========== AFTER INCIDENT ==========")

print(
    "Location:",
    location
)

print(
    "Risk Score:",
    after_row["risk_score"]
)

print(
    "Risk Level:",
    after_row["risk_level"]
)

print(
    "Traffic Density:",
    after_row["traffic_density"]
)

print(
    "Current Incident:",
    after_row["current_incidents"]
)


print("\n========== CHANGE ==========")

print(
    "Risk Change:",
    round(
        after_row["risk_score"]
        - before_row["risk_score"],
        2
    )
)
