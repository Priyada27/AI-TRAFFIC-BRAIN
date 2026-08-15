import streamlit as st
import pandas as pd
import folium
import plotly.express as px

from streamlit_folium import st_folium

from risk_engine import add_risk_analysis
from deployment import recommend_deployment
from incident_simulator import (
    simulate_incident,
    get_incident_description
)


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

    **AI Traffic Brain** continuously identifies where traffic risk is
    highest, explains why the risk is high, and recommends how limited
    traffic personnel should be deployed — while keeping the final
    decision with the human authority.
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

    st.error(
        f"Error loading dataset: {e}"
    )

    st.stop()


# ============================================================
# RISK ENGINE
# ============================================================

try:

    df = add_risk_analysis(df)

except Exception as e:

    st.error(
        "Risk Engine could not process the dataset."
    )

    st.exception(e)

    st.stop()


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

required_columns = [
    "risk_score",
    "risk_level",
    "police_officers",
    "current_incidents"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    st.warning(
        "The following columns are missing from the dataset:"
    )

    st.write(missing_columns)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Traffic Control Panel")

st.sidebar.markdown(
    "Simulate traffic authority decisions using the controls below."
)

total_dataset_officers = int(
    df["police_officers"].sum()
) if "police_officers" in df.columns else 50

available_officers = st.sidebar.slider(
    "👮 Available Traffic Police",
    min_value=1,
    max_value=max(total_dataset_officers, 50),
    value=min(30, max(total_dataset_officers, 50)),
    step=1
)

st.sidebar.divider()

st.sidebar.subheader("📊 Dataset Information")

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

    risk_levels = (
        df["risk_level"]
        .astype(str)
        .str.upper()
    )

    critical_count = (
        risk_levels == "CRITICAL"
    ).sum()

    high_count = (
        risk_levels == "HIGH"
    ).sum()

else:

    critical_count = 0
    high_count = 0

# ============================================================
# OPERATIONAL KPI CALCULATIONS
# ============================================================

if "current_incidents" in df.columns:

    active_incidents = int(
        (df["current_incidents"] > 0).sum()
    )

else:

    active_incidents = 0


# The sidebar slider is the single source of truth
# for the currently available deployment pool.
total_police_officers = available_officers


# ============================================================
# TRAFFIC RISK OVERVIEW
# ============================================================

st.subheader("📊 Traffic Risk Overview")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

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

with col6:

    st.metric(
        "🚨 Active Incidents",
        active_incidents
    )


with col7:

    st.metric(
        "👮 Police Officers",
        total_police_officers
    )


st.divider()


# ============================================================
# LIVE AI TRAFFIC STATUS
# ============================================================

# Determine the overall traffic condition using multiple
# network-level AI indicators.

if (
    critical_count > 0
    or average_risk >= 70
):
    traffic_status = "🚨 CRITICAL"
    traffic_status_message = (
        "Critical traffic conditions detected. "
        "Immediate traffic intervention may be required."
    )

elif (
    highest_risk >= 70
    or high_count >= 5
):
    traffic_status = "🔴 HIGH"
    traffic_status_message = (
        "Elevated traffic risk detected across multiple locations. "
        "Increased monitoring and police deployment may be required."
    )

elif average_risk >= 50:
    traffic_status = "🟡 MODERATE"
    traffic_status_message = (
        "Moderate traffic risk detected. "
        "Traffic conditions should be actively monitored."
    )

else:
    traffic_status = "🟢 NORMAL"
    traffic_status_message = (
        "Traffic conditions are currently stable."
    )


st.subheader("🧠 Live AI Traffic Status")

status_col1, status_col2 = st.columns([1, 3])

with status_col1:

    st.metric(
        "Current Traffic Status",
        traffic_status
    )

with status_col2:

    st.info(
        f"""
        **AI Assessment:** {traffic_status_message}

        Average Risk: **{average_risk:.2f}** |
        Highest Risk: **{highest_risk:.2f}** |
        High-Risk Locations: **{high_count}** |
        Critical Locations: **{critical_count}** |
        Active Incidents: **{active_incidents}**
        """
    )


st.divider()


# ============================================================
# OPERATIONAL TRAFFIC STATUS
# ============================================================

st.subheader("🚦 Operational Traffic Status")

if "traffic_density" in df.columns:

    average_density = df["traffic_density"].mean()

    maximum_density = df["traffic_density"].max()

else:

    average_density = 0
    maximum_density = 0


if "peak_activity" in df.columns:

    average_peak_activity = df["peak_activity"].mean()

else:

    average_peak_activity = 0


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "🚗 Average Traffic Density",
        f"{average_density:.1f}%"
    )

with col2:

    st.metric(
        "🔴 Maximum Traffic Density",
        f"{maximum_density:.1f}%"
    )

with col3:

    st.metric(
        "📈 Average Peak Activity",
        f"{average_peak_activity:.1f}%"
    )


st.divider()


# ============================================================
# TRAFFIC RISK DISTRIBUTION
# ============================================================

st.subheader("📊 Traffic Risk Distribution")

if "risk_level" in df.columns:

    risk_distribution = (
        df["risk_level"]
        .astype(str)
        .str.upper()
        .value_counts()
        .reindex(
            ["CRITICAL", "HIGH", "MODERATE"],
            fill_value=0
        )
        .reset_index()
    )

    risk_distribution.columns = [
        "Risk Level",
        "Locations"
    ]

    fig = px.bar(
        risk_distribution,
        x="Risk Level",
        y="Locations",
        text="Locations",
        title="Traffic Risk Level Distribution",
        category_orders={
            "Risk Level": [
                "CRITICAL",
                "HIGH",
                "MODERATE"
            ]
        }
    )

    fig.update_traces(
        textposition="outside",
        marker_line_width=1.5,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Locations: %{y}<extra></extra>"
        )
    )

    fig.update_layout(
        height=450,
        template="plotly_white",
        xaxis_title="Risk Level",
        yaxis_title="Number of Locations",
        showlegend=False,
        margin=dict(
            l=40,
            r=40,
            t=80,
            b=40
        ),
        transition={
            "duration": 800,
            "easing": "cubic-in-out"
        }
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

else:

    st.warning(
        "Risk level data is not available."
    )


st.divider()


# ============================================================
# HIGHEST RISK LOCATIONS
# ============================================================

st.subheader("🚨 Highest Traffic Risk Locations")

if (
    "risk_score" in df.columns
    and "location" in df.columns
):

    # --------------------------------------------------------
    # Calculate AI deployment using the sidebar police slider
    # --------------------------------------------------------

    highest_risk_deployment = recommend_deployment(
        df,
        available_officers
    )

    top_risk = (
        highest_risk_deployment
        .sort_values(
            "risk_score",
            ascending=False
        )
        .head(10)
    )

    risk_display_columns = [
        column
        for column in [
            "location",
            "risk_score",
            "risk_level",
            "traffic_density",
            "current_incidents",
            "police_officers",
            "recommended_officers"
        ]
        if column in top_risk.columns
    ]

    # Rename columns so the distinction is clear
    top_risk_display = top_risk[
        risk_display_columns
    ].rename(
        columns={
            "police_officers": "Current Police",
            "recommended_officers": "AI Recommended Deployment"
        }
    )

    st.dataframe(
        top_risk_display,
        width="stretch",
        hide_index=True
    )

else:

    st.warning(
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

    # Use simulated traffic data when an incident simulation exists.
    # Otherwise use the original dataset.
    map_df = st.session_state.get(
        "simulated_df",
        df
    )

    for _, row in map_df.iterrows():

        risk = float(
            row["risk_score"]
        )

        # ====================================================
        # AI RISK MAP COLOR
        # ====================================================

        risk_level = str(
            row.get(
                "risk_level",
                "MODERATE"
            )
        ).upper()

        if risk_level == "CRITICAL":

            marker_color = "red"

        elif risk_level == "HIGH":

            marker_color = "orange"

        elif risk_level == "MODERATE":

            marker_color = "green"

        else:

            marker_color = "blue"


        location_name = str(
            row.get(
                "location",
                "Unknown"
            )
        )

        popup_html = f"""
        <b>{location_name}</b><br>
        Risk Score: {risk:.2f}<br>
        Risk Level: {risk_level}
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
                popup_html,
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
        "Latitude/longitude columns are not available, "
        "so the map cannot be displayed."
    )


st.divider()


# ============================================================
# INCIDENT SIMULATOR
# ============================================================

st.header("🚨 Traffic Incident Simulator")

st.markdown(
    """
    Simulate a sudden traffic incident and observe how the
    AI Traffic Brain recalculates traffic risk and deployment
    priority.
    """
)

simulation_enabled = st.checkbox(
    "Enable Incident Simulation",
    key="simulation_enabled"
)

if simulation_enabled:

    simulation_location = st.selectbox(
        "📍 Select Incident Location",
        df["location"].tolist(),
        key="simulation_location_select"
    )

    incident_type = st.selectbox(
        "🚨 Incident Type",
        [
            "Major Accident",
            "Minor Accident",
            "Road Blockage",
            "Traffic Jam",
            "Emergency Vehicle Movement"
        ],
        key="incident_type_select"
    )

    incident_severity = st.slider(
        "⚠️ Incident Severity",
        min_value=1,
        max_value=10,
        value=5,
        key="incident_severity_select"
    )

    if st.button(
        "🚨 Simulate Incident",
        type="primary",
        key="simulate_incident_button"
    ):

        try:

            # =================================================
            # BEFORE INCIDENT
            # =================================================

            before_df = add_risk_analysis(
                df.copy()
            )

            before_deployment = recommend_deployment(
                before_df,
                available_officers
            )

            before_matches = before_deployment[
                before_deployment["location"]
                == simulation_location
            ]

            if before_matches.empty:

                st.error(
                    "Selected location was not found."
                )

            else:

                before_row = before_matches.iloc[0]

                # =============================================
                # SIMULATE INCIDENT
                # =============================================

                simulated_df = simulate_incident(
                    df=df,
                    location=simulation_location,
                    incident_type=incident_type,
                    severity=incident_severity
                )

                # =============================================
                # RECALCULATE RISK
                # =============================================

                simulated_df = add_risk_analysis(
                    simulated_df
                )

                # =============================================
                # RECALCULATE DEPLOYMENT
                # =============================================

                simulated_deployment = recommend_deployment(
                    simulated_df,
                    available_officers
                )

                after_matches = simulated_deployment[
                    simulated_deployment["location"]
                    == simulation_location
                ]

                if after_matches.empty:

                    st.error(
                        "Simulated location was not found."
                    )

                else:

                    after_row = after_matches.iloc[0]

                    # =========================================
                    # SAVE SIMULATION STATE
                    # =========================================

                    st.session_state[
                        "simulated_df"
                    ] = simulated_df

                    st.session_state[
                        "simulated_deployment"
                    ] = simulated_deployment

                    st.session_state[
                        "simulation_location"
                    ] = simulation_location

                    st.session_state[
                        "incident_type"
                    ] = incident_type

                    st.session_state[
                        "incident_severity"
                    ] = incident_severity

                    st.session_state[
                        "before_row"
                    ] = before_row.to_dict()

                    st.session_state[
                        "after_row"
                    ] = after_row.to_dict()

                    st.success(
                        f"🚨 {incident_type} simulated at "
                        f"**{simulation_location}**"
                    )

        except Exception as e:

            st.error(
                "Simulation failed."
            )

            st.exception(e)


# ============================================================
# SIMULATION RESULTS
# ============================================================

if (
    "simulated_deployment" in st.session_state
    and "simulation_location" in st.session_state
    and "before_row" in st.session_state
    and "after_row" in st.session_state
):

    st.subheader(
        "📈 AI Response to Incident"
    )

    simulation_location = st.session_state[
        "simulation_location"
    ]

    incident_name = st.session_state.get(
        "incident_type",
        "Traffic Incident"
    )

    incident_severity_value = st.session_state.get(
        "incident_severity",
        0
    )

    before_row = st.session_state[
        "before_row"
    ]

    after_row = st.session_state[
        "after_row"
    ]

    # ========================================================
    # BEFORE VALUES
    # ========================================================

    before_risk = float(
        before_row["risk_score"]
    )

    before_level = str(
        before_row["risk_level"]
    )

    before_priority = float(
        before_row["priority_score"]
    )

    before_officers = int(
        before_row["recommended_officers"]
    )

    # ========================================================
    # AFTER VALUES
    # ========================================================

    after_risk = float(
        after_row["risk_score"]
    )

    after_level = str(
        after_row["risk_level"]
    )

    after_priority = float(
        after_row["priority_score"]
    )

    after_officers = int(
        after_row["recommended_officers"]
    )

    # ========================================================
    # CHANGES
    # ========================================================

    risk_change = round(
        after_risk - before_risk,
        2
    )

    priority_change = round(
        after_priority - before_priority,
        2
    )

    officer_change = (
        after_officers - before_officers
    )

    # ========================================================
    # INCIDENT DESCRIPTION
    # ========================================================

    description = get_incident_description(
        incident_name,
        incident_severity_value
    )

    st.info(
        f"""
        **🚨 Incident Description**

        {description}
        """
    )

    # ========================================================
    # KEY METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📍 Location",
            simulation_location
        )

    with col2:

        st.metric(
            "⚠️ Risk Score",
            f"{after_risk:.2f}",
            delta=f"{risk_change:+.2f}"
        )

    with col3:

        st.metric(
            "🎯 Priority Score",
            f"{after_priority:.2f}",
            delta=f"{priority_change:+.2f}"
        )

    with col4:

        st.metric(
            "🚓 AI Recommended Deployment",
            after_officers,
            delta=f"{officer_change:+d}"
        )

    # ========================================================
    # BEFORE VS AFTER
    # ========================================================

    st.subheader(
        "🔄 Before vs After Incident"
    )

    comparison_df = pd.DataFrame(
        {
            "Metric": [
                "Risk Score",
                "Risk Level",
                "Priority Score",
                "AI Recommended Deployment"
            ],
            "Before Incident": [
                f"{before_risk:.2f}",
                before_level,
                f"{before_priority:.2f}",
                before_officers
            ],
            "After Incident": [
                f"{after_risk:.2f}",
                after_level,
                f"{after_priority:.2f}",
                after_officers
            ]
        }
    )

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True
    )

    # ========================================================
    # AI DECISION SUMMARY
    # ========================================================

    st.subheader(
        "🧠 AI Decision Summary"
    )

    if risk_change > 0:

        st.warning(
            f"""
            **Risk increased by {risk_change:.2f} points.**

            A **{incident_name.lower()}** with severity
            **{incident_severity_value}/10** was simulated at
            **{simulation_location}**.

            **Risk transition:**

            {before_risk:.2f} ({before_level})
            → {after_risk:.2f} ({after_level})

            **Priority transition:**

            {before_priority:.2f}
            → {after_priority:.2f}

            **Police recommendation:**

            {before_officers}
            → {after_officers}

            The AI recalculated the location's risk and
            deployment priority using the updated traffic
            conditions.

            The final deployment decision remains with the
            authorized traffic authority.
            """
        )

    elif risk_change < 0:

        st.success(
            f"""
            **Risk decreased by {abs(risk_change):.2f} points.**

            The AI recalculated the location after the
            simulated incident.
            """
        )

    else:

        st.info(
            """
            **No change in calculated risk score.**

            The simulated conditions did not change the
            final weighted risk score.
            """
        )

    # ========================================================
    # UPDATED DEPLOYMENT
    # ========================================================

    st.subheader(
        "🚓 Updated Deployment Recommendation"
    )

    simulated_deployment = st.session_state[
        "simulated_deployment"
    ]

    simulation_display_columns = [
        column
        for column in [
            "location",
            "risk_score",
            "risk_level",
            "priority_score",
            "recommended_officers"
        ]
        if column in simulated_deployment.columns
    ]

    st.dataframe(
        simulated_deployment[
            simulation_display_columns
        ],
        width="stretch",
        hide_index=True
    )

    # ========================================================
    # RESET
    # ========================================================

    if st.button(
        "🔄 Reset Simulation",
        key="reset_simulation_button"
    ):

        simulation_keys = [
            "simulated_df",
            "simulated_deployment",
            "simulation_location",
            "incident_type",
            "incident_severity",
            "before_row",
            "after_row"
        ]

        for key in simulation_keys:

            if key in st.session_state:

                del st.session_state[key]

        st.rerun()


st.divider()


# ============================================================
# AI POLICE DEPLOYMENT ENGINE
# ============================================================

st.header("👮 AI Police Deployment")

st.markdown(
    """
    The AI Deployment Engine prioritizes locations according to
    traffic risk, police coverage and current incidents.

    It recommends how limited traffic personnel should be
    distributed across high-priority locations.
    """
)

st.info(
    f"👮 Currently Available Traffic Police: "
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


deployment_result = None


if deployment_columns_available:

    try:

        deployment_result = recommend_deployment(
            df,
            available_officers
        )

        st.subheader(
            "🚨 AI Police Deployment"
        )

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

        deployment_display = deployment_result[
            deployment_display_columns
        ].rename(
            columns={
                "police_officers": "Current Police",
                "recommended_officers": "AI Recommended Deployment"
            }
        )

        st.dataframe(
            deployment_display,
            width="stretch",
            hide_index=True
        )

    except Exception as e:

        st.error(
            "Police Deployment Engine encountered an error."
        )

        st.exception(e)

else:

    st.warning(
        "Police deployment cannot be calculated because "
        "required dataset columns are missing."
    )


# ============================================================
# AI DEPLOYMENT PRIORITY CHART
# ============================================================

st.subheader("🎯 AI Deployment Priority")

if (
    deployment_result is not None
    and not deployment_result.empty
    and "priority_score" in deployment_result.columns
    and "location" in deployment_result.columns
):

    chart_data = (
        deployment_result
        .sort_values(
            "priority_score",
            ascending=False
        )
        .head(10)
        .copy()
    )

    # --------------------------------------------------------
    # Add AI ranking
    # --------------------------------------------------------

    chart_data["Rank"] = range(
        1,
        len(chart_data) + 1
    )

    chart_data["Rank Label"] = chart_data["Rank"].map(
        lambda rank:
            "🥇" if rank == 1
            else "🥈" if rank == 2
            else "🥉" if rank == 3
            else f"#{rank}"
    )

    chart_data["Risk Score"] = chart_data[
        "risk_score"
    ].round(2)

    chart_data["Priority Score"] = chart_data[
        "priority_score"
    ].round(2)

    chart_data["AI Recommended Deployment"] = chart_data[
        "recommended_officers"
    ].astype(int)

    # Reverse for highest priority at the top
    chart_data = chart_data.sort_values(
        "Priority Score",
        ascending=True
    )

    fig = px.bar(
        chart_data,
        x="Priority Score",
        y="location",
        orientation="h",
        text="Priority Score",
        custom_data=[
            "Risk Score",
            "AI Recommended Deployment",
            "Rank Label"
        ],
        title="🎯 Top High-Priority Traffic Locations"
    )

    fig.update_traces(
        textposition="outside",
        marker_line_width=1.5,
        hovertemplate=(
            "<b>%{customdata[2]} %{y}</b><br>"
            "AI Priority Score: %{x:.2f}<br>"
            "Traffic Risk: %{customdata[0]:.2f}<br>"
            "AI Recommended Deployment: "
            "%{customdata[1]}<extra></extra>"
        )
    )

    fig.update_layout(
        height=550,
        template="plotly_white",
        xaxis_title="AI Priority Score",
        yaxis_title="Location",
        showlegend=False,
        margin=dict(
            l=40,
            r=100,
            t=80,
            b=40
        ),
        transition={
            "duration": 900,
            "easing": "cubic-in-out"
        }
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

else:

    st.warning(
        "AI deployment priority data is not available."
    )


st.divider()


# DEPLOYMENT SUMMARY
# ============================================================

if (
    deployment_result is not None
    and not deployment_result.empty
):

    st.subheader(
        "📌 Deployment Summary"
    )

    total_deployed = int(
        deployment_result[
            "recommended_officers"
        ].sum()
    )

    remaining_officers = max(
        available_officers - total_deployed,
        0
    )

    deployment_locations = int(
        (
            deployment_result[
                "recommended_officers"
            ] > 0
        ).sum()
    )


    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "👮 Available Traffic Police",
            available_officers
        )

    with col2:

        st.metric(
            "🚓 AI Recommended Deployment",
            total_deployed
        )

    with col3:

        st.metric(
            "🟢 Remaining Officers",
            remaining_officers
        )

    with col4:

        st.metric(
            "📍 Locations Covered",
            deployment_locations
        )


st.divider()


# ============================================================
# AI DECISION EXPLANATION
# ============================================================

st.subheader(
    "🧠 AI Decision Explanation"
)


if (
    deployment_result is not None
    and not deployment_result.empty
):

    # --------------------------------------------------------
    # Find highest priority location
    # --------------------------------------------------------

    top_location = (
        deployment_result
        .sort_values(
            "priority_score",
            ascending=False
        )
        .iloc[0]
    )


    # --------------------------------------------------------
    # Extract values safely
    # --------------------------------------------------------

    location_name = str(
        top_location.get(
            "location",
            "Unknown Location"
        )
    )

    risk_value = float(
        top_location.get(
            "risk_score",
            0
        )
    )

    priority_value = float(
        top_location.get(
            "priority_score",
            0
        )
    )

    current_police = int(
        top_location.get(
            "police_officers",
            0
        )
    )

    recommended = int(
        top_location.get(
            "recommended_officers",
            0
        )
    )

    risk_level = str(
        top_location.get(
            "risk_level",
            "UNKNOWN"
        )
    )


    # --------------------------------------------------------
    # Main recommendation
    # --------------------------------------------------------

    st.success(
        f"🎯 **Highest Deployment Priority: "
        f"{location_name}**"
    )


    # --------------------------------------------------------
    # Explanation metrics
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "⚠️ Traffic Risk",
            f"{risk_value:.2f}"
        )

    with col2:

        st.metric(
            "🎯 Priority Score",
            f"{priority_value:.2f}"
        )

    with col3:

        st.metric(
            "👮 Current Police",
            current_police
        )

    with col4:

        st.metric(
            "🚓 AI Recommended Deployment",
            recommended
        )


    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    st.markdown(
        "### 🔍 Why did the AI select this location?"
    )

    st.write(
        f"""
        **{location_name}** has been identified as the
        highest deployment priority by the AI Traffic Brain.

        The system calculated a **traffic risk score of
        {risk_value:.2f}** and a **deployment priority score
        of {priority_value:.2f}**.

        The location is currently classified as
        **{risk_level} risk**.

        Based on these factors, the AI recommends
        deploying **{recommended} additional traffic police
        personnel** to this location from the available
        deployment pool.
        """
    )


    # --------------------------------------------------------
    # Human authority statement
    # --------------------------------------------------------

    st.info(
        "👤 **Human Authority:** "
        "The AI recommendation is decision support only. "
        "The authorized traffic authority retains the final "
        "decision to accept, modify, or reject the deployment."
    )


else:

    st.warning(
        "⚠️ AI decision explanation is currently unavailable "
        "because deployment results could not be calculated."
    )


st.divider()


# ============================================================
# DATA EXPLORER
# ============================================================

with st.expander(
    "📋 View Complete Traffic Dataset"
):

    st.dataframe(
        df,
        width="stretch",
        hide_index=True
    )


# ============================================================
# PROJECT WORKFLOW
# ============================================================

with st.expander(
    "⚙️ How AI Traffic Brain Works"
):

    st.markdown(
        """
        ### AI Traffic Brain Workflow

        **1. Traffic Data**

        Traffic conditions, incidents, police availability,
        location and other parameters are collected.

        ↓

        **2. Risk Engine**

        The system calculates a traffic risk score for
        every monitored location.

        ↓

        **3. Risk Classification**

        Locations are classified into risk levels such as
        LOW, MODERATE, HIGH and CRITICAL.

        ↓

        **4. Deployment Engine**

        The system considers risk, police coverage and
        current incidents to calculate deployment priority.

        ↓

        **5. Police Recommendation**

        Limited traffic personnel are distributed to the
        highest-priority locations.

        ↓

        **6. Incident Simulation**

        A simulated accident or traffic incident changes
        the traffic conditions.

        ↓

        **7. AI Recalculation**

        Risk and deployment priority are recalculated.

        ↓

        **8. Human Decision**

        The final deployment decision remains with the
        authorized traffic authority.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🚦 AI Traffic Brain "
)

st.caption(
    "AI provides recommendations. Final deployment decisions "
    "remain with authorized human traffic authorities."
)
