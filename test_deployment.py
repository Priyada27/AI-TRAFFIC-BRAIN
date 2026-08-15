import pandas as pd

from risk_engine import add_risk_analysis
from deployment import recommend_deployment


df = pd.read_csv(
    "data/nagpur_traffic.csv"
)

df = add_risk_analysis(df)

result = recommend_deployment(
    df,
    available_officers=10
)

print(
    result[
        [
            "location",
            "risk_score",
            "risk_level",
            "priority_score",
            "recommended_officers"
        ]
    ].head(10)
)
