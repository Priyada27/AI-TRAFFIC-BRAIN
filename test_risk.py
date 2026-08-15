import pandas as pd

from risk_engine import add_risk_analysis


df = pd.read_csv("data/nagpur_traffic.csv")

df = add_risk_analysis(df)

print(
    df[
        [
            "location",
            "risk_score",
            "risk_level"
        ]
    ].sort_values(
        "risk_score",
        ascending=False
    )
)
