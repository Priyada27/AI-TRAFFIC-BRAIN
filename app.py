import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium

from risk_engine import add_risk_analysis
from deployment import recommend_deployment


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Traffic Brain",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .main {
            padding-top: 1rem;
        }

        .block-container {
            padding-top: 1.5rem;
        }

        .metric-card {
            background-color: #f8f9fa;
            padding: 18px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e5e7eb;
        }

        .risk-high {
            color: #dc2626;
            font-weight: bold;
        }

        .risk-medium {
            color: #f59e0b;
            font-weight: bold;
        }

        .risk-low {
            color: #16a34a;
            font-weight: bold;
        }

        .recommendation {
            background-color: #fff7ed;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #f97316;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.title("🚦 AI Traffic Brain")

st.markdown(
    """
    ### AI-Based Traffic Risk & Police Deployment Decision Support System

    **AI Traffic Brain** continuously identifies where traffic risk is highest,
    explains the major risk factors, and recommends how limited traffic
    personnel should be deployed — while keeping the final decision with
    the human authority.
    """
)

st.divider()


# ============================================================
# LOAD DATASET
# ============================================================

DATA_PATH = "data/nagpur_traffic.csv"

try:
    df = pd.read_csv(DATA_PATH)

except FileNotFoundError:
    st.error(
        f"Dataset not found: `{DATA_PATH}`"
    )

    st.info(
        "Make sure `nagpur_traffic.csv` exists inside the `data` folder."
    )

    st.stop()

except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# ============================================================
# RISK ENGINE
# ============================================================

try:
    df = add_risk_analysis(df)

except Exception as e:
    st.error("Risk Engine could not process the dataset.")
    st.exception(e)
    st.stop()


# ============================================================
# BASIC DATA VALIDATION
# ============================================================

required_for_deployment = [
    "risk_score",
    "risk_level",
    "police_officers",
    "current_incidents"
]

missing_columns = [
    column
    for column in required_for_deployment
    if column not in df.columns
]

if missing_columns:

    st.warning(
        "Some deployment columns are missing from the dataset:"
    )

    st.write(missing_columns)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Traffic Control Panel")

st.sidebar.markdown(
    "Use the controls below to simulate traffic authority decisions."
)

available_officers = st.sidebar.slider(
    "👮 Available Traffic Police",
    min_value=1,
    max_value=50,
    value=10,
    step=1
)

st.sidebar.divider()

st.sidebar.subheader("📊 Dataset")

st.sidebar.write(
    f"Locations: **{len(df)}**"
)

if "risk_score" in df.columns:
    st.sidebar.write(
        f"Average Risk: **{df['risk_score'].mean():.2f}**"
    )


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_locations = len(df)

if "risk_score" in df.columns:

    average_risk = df["risk_score"].mean()

    highest_risk = df["risk_score"].max()

else:

    average_risk = 0
    highest_risk = 0


if "risk_level" in df.columns:

    critical_count = (
        df["risk_level"]
        .astype(str)
        .str.upper()
        .isin(["CRITICAL"])
        .sum()
    )

    high_count = (
        df["risk_level"]
        .astype(str)
        .str.upper()
        .isin(["HIGH"])
        .sum()
    )

else:

    critical_count = 0
    high_count = 0


# ============================================================
# KPI DASHBOARD
# ============================================================

st.subheader("📊 Traffic Risk Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "📍 Locations",
        total_locations
    )

with col2:
    st.metric(
        "⚠️ Average Risk",
        f"{average_risk:.2f}"
    )

with col3:
    st.metric(
        "🔴 Highest Risk",
        f"{highest_risk:.2f}"
    )

with col4:
    st.metric(
        "🚨 High Risk",
        high_count
    )

with col5:
    st.metric(
        "🔴 Critical",
        critical_count
    )


st.divider()


# ============================================================
# TOP RISK LOCATIONS
# ============================================================

st.subheader("🚨 Highest Traffic Risk Locations")

if "risk_score" in df.columns and "location" in df.columns:

    top_risk = df.sort_values(
        "risk_score",
        ascending=False
    ).head(10)

    display_columns = [
        column
        for column in [
            "location",
            "risk_score",
            "risk_level",
            "traffic_density",
            "avg_speed",
            "current_incidents",
            "police_officers"
        ]
        if column in top_risk.columns
    ]

    st.dataframe(
        top_risk[display_columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Risk/location columns are not available."
    )


st.divider()


# ============================================================
# TRAFFIC RISK MAP
# ============================================================

st.subheader("🗺️ Nagpur Traffic Risk Map")

if (
    "latitude" in df.columns
    and "longitude" in df.columns
    and "risk_score" in df.columns
):

    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    traffic_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=11
    )

    for _, row in df.iterrows():

        risk = float(row["risk_score"])

        if risk >= 80:
            marker_color = "red"

        elif risk >= 60:
            marker_color = "orange"

        else:
            marker_color = "green"

        popup_text = f"""
        <b>{row.get('location', 'Unknown')}</b><br>
        Risk Score: {risk:.2f}<br>
        Risk Level: {row.get('risk_level', 'N/A')}
        """

        folium.CircleMarker(
            location=[
                row["latitude"],
                row["longitude"]
            ],
            radius=8,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.75,
            popup=folium.Popup(
                popup_text,
                max_width=300
            )
        ).add_to(traffic_map)

    st_folium(
        traffic_map,
        width=None,
        height=550
    )

else:

    st.warning(
        "Latitude/longitude columns are not available in the dataset, "
        "so the map cannot be displayed."
    )


st.divider()


# ============================================================
# POLICE DEPLOYMENT ENGINE
# ============================================================

st.header("👮 AI Police Deployment")

st.markdown(
    """
    The deployment engine prioritizes high-risk locations and recommends
    where limited traffic police personnel should be deployed.
    """
)

st.info(
    f"Currently available traffic police personnel: "
    f"**{available_officers}**"
)


# ============================================================
# DEPLOYMENT CALCULATION
# ============================================================

deployment_columns_available = all(
    column in df.columns
    for column in [
        "risk_score",
        "police_officers",
        "current_incidents"
    ]
)

if deployment_columns_available:

    try:

        deployment_result = recommend_deployment(
            df,
            available_officers
        )

        st.subheader("🚨 Recommended Deployment")

        deployment_display_columns = [
            column
            for column in [
                "location",
                "risk_score",
                "risk_level",
                "priority_score",
                "recommended_officers"
            ]
            if column in deployment_result.columns
        ]

        st.dataframe(
            deployment_result[
                deployment_display_columns
            ],
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error(
            "Police Deployment Engine encountered an error."
        )

        st.exception(e)

else:

    st.warning(
        "Deployment cannot be calculated because required columns "
        "are missing from the dataset."
    )


# ============================================================
# DEPLOYMENT SUMMARY
# ============================================================

if (
    deployment_columns_available
    and "deployment_result" in locals()
):

    st.subheader("📌 Deployment Summary")

    total_deployed = int(
        deployment_result[
            "recommended_officers"
        ].sum()
    )

    remaining_officers = max(
        available_officers - total_deployed,
        0
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "👮 Available",
            available_officers
        )

    with col2:

        st.metric(
            "🚓 Recommended",
            total_deployed
        )

    with col3:

        st.metric(
            "🟢 Remaining",
            remaining_officers
        )


# ============================================================
# DECISION SUPPORT EXPLANATION
# ============================================================

st.divider()

st.subheader("🧠 AI Decision Explanation")

if (
    deployment_columns_available
    and "deployment_result" in locals()
):

    top_location = deployment_result.iloc[0]

    location_name = top_location.get(
        "location",
        "Unknown location"
    )

    risk_value = top_location.get(
        "risk_score",
        0
    )

    priority_value = top_location.get(
        "priority_score",
        0
    )

    recommended = top_location.get(
        "recommended_officers",
        0
    )

    st.markdown(
        f"""
        <div class="recommendation">

        <b>Highest deployment priority:</b>
        {location_name}

        <br><br>

        <b>Risk Score:</b>
        {risk_value:.2f}

        <br>

        <b>Priority Score:</b>
        {priority_value:.2f}

        <br>

        <b>Recommended Police:</b>
        {recommended}

        <br><br>

        <b>Reason:</b>
        This location has a high calculated traffic risk and therefore
        receives higher deployment priority.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA EXPLORER
# ============================================================

st.divider()

with st.expander("📋 View Traffic Dataset"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🚦 AI Traffic Brain"
)

st.caption(
    "AI provides recommendations. Final deployment decisions remain "
    "with authorized human traffic authorities."
)
