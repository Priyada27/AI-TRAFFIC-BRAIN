import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium

from risk_engine import add_risk_analysis


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Traffic Brain",
    page_icon="🚦",
    layout="wide"
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():

    df = pd.read_csv(
        "data/nagpur_traffic.csv"
    )

    df = add_risk_analysis(df)

    return df


df = load_data()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🚦 AI Traffic Brain")

st.subheader(
    "AI-Based Traffic Risk Heatmap & "
    "Police Deployment Decision Support System"
)

st.caption(
    "Prototype using simulated traffic data for Nagpur"
)


# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

total_locations = len(df)

critical_locations = len(
    df[df["risk_level"] == "CRITICAL"]
)

high_risk_locations = len(
    df[df["risk_level"] == "HIGH"]
)

total_officers = df["police_officers"].sum()


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "📍 Locations",
        total_locations
    )


with col2:
    st.metric(
        "🔴 Critical",
        critical_locations
    )


with col3:
    st.metric(
        "🟠 High Risk",
        high_risk_locations
    )


with col4:
    st.metric(
        "👮 Officers",
        total_officers
    )


st.divider()


# --------------------------------------------------
# RISK RANKING
# --------------------------------------------------

st.subheader("🔥 Highest Risk Locations")


top_locations = df.sort_values(
    "risk_score",
    ascending=False
).head(10)


st.dataframe(
    top_locations[
        [
            "location",
            "risk_score",
            "risk_level",
            "traffic_density",
            "accident_history",
            "traffic_violations",
            "police_officers"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# NAGPUR MAP
# --------------------------------------------------

st.subheader("🗺️ Nagpur Traffic Risk Heatmap")


center_lat = df["latitude"].mean()
center_lon = df["longitude"].mean()


m = folium.Map(
    location=[
        center_lat,
        center_lon
    ],
    zoom_start=12
)


# --------------------------------------------------
# ADD LOCATIONS TO MAP
# --------------------------------------------------

for _, row in df.iterrows():

    if row["risk_level"] == "CRITICAL":
        color = "red"

    elif row["risk_level"] == "HIGH":
        color = "orange"

    elif row["risk_level"] == "MODERATE":
        color = "blue"

    else:
        color = "green"


    popup_text = f"""
    <b>{row['location']}</b><br>
    Risk Score: {row['risk_score']}<br>
    Risk Level: {row['risk_level']}<br>
    Traffic Density: {row['traffic_density']}<br>
    Accident History: {row['accident_history']}<br>
    Violations: {row['traffic_violations']}<br>
    Police Officers: {row['police_officers']}
    """


    folium.CircleMarker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        radius=9,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(
            popup_text,
            max_width=300
        )
    ).add_to(m)


st_folium(
    m,
    width=1200,
    height=600
)


# --------------------------------------------------
# LOCATION DETAILS
# --------------------------------------------------

st.divider()

st.subheader("🔎 Location Risk Analysis")


selected_location = st.selectbox(
    "Select a location",
    df["location"].tolist()
)


selected = df[
    df["location"] == selected_location
].iloc[0]


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Risk Score",
        selected["risk_score"]
    )


with col2:

    st.metric(
        "Risk Level",
        selected["risk_level"]
    )


with col3:

    st.metric(
        "Police Officers",
        selected["police_officers"]
    )


st.write(
    "### Risk Factors"
)

st.write(
    f"Traffic Density: "
    f"{selected['traffic_density']}"
)

st.write(
    f"Accident History: "
    f"{selected['accident_history']}"
)

st.write(
    f"Traffic Violations: "
    f"{selected['traffic_violations']}"
)

st.write(
    f"Current Incidents: "
    f"{selected['current_incidents']}"
)

st.write(
    f"Road Obstruction: "
    f"{selected['road_obstruction']}"
)

st.write(
    f"Weather Risk: "
    f"{selected['weather_risk']}"
)
