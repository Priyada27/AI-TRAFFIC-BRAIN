import streamlit as st
import pandas as pd
import folium

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

available_officers = st.sidebar.slider(
    "👮 Available Traffic Police",
    min_value=1,
    max_value=50,
    value=10,
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


if "police_officers" in df.columns:

    total_police_officers = int(
        df["police_officers"].sum()
    )

else:

    total_police_officers = 0


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
# HIGHEST RISK LOCATIONS
# ============================================================

st.subheader("🚨 Highest Traffic Risk Locations")

if (
    "risk_score" in df.columns
    and "location" in df.columns
):

    top_risk = (
        df
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
            "avg_speed",
            "current_incidents",
            "police_officers"
        ]
        if column in top_risk.columns
    ]

    st.dataframe(
        top_risk[
            risk_display_columns
        ],
        use_container_width=True,
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

    for _, row in df.iterrows():

        risk = float(
            row["risk_score"]
        )

        if risk >= 80:

            marker_color = "red"

        elif risk >= 60:

            marker_color = "orange"

        else:

            marker_color = "green"

        location_name = str(
            row.get(
                "location",
                "Unknown"
            )
        )

        risk_level = str(
            row.get(
                "risk_level",
                "N/A"
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
            "👮 Recommended Police",
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
                "Recommended Police"
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
        use_container_width=True,
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
        use_container_width=True,
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
            "🚨 Recommended Police Deployment"
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
        "Police deployment cannot be calculated because "
        "required dataset columns are missing."
    )


# ============================================================
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


    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "👮 Available Officers",
            available_officers
        )

    with col2:

        st.metric(
            "🚓 Recommended Deployment",
            total_deployed
        )

    with col3:

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

    col1, col2, col3 = st.columns(3)

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
            "👮 Recommended Police",
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

        Based on these factors, the system recommends
        deploying **{recommended} traffic police personnel**
        to this location.
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
        use_container_width=True,
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
