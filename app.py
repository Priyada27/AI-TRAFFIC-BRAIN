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
# ACTIVE TRAFFIC DATA
# ============================================================
# After incident simulation, ALL dashboard sections use the
# simulated dataframe. Otherwise they use the original data.

active_df = st.session_state.get(
    "simulated_df",
    df
).copy()


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

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
    f"Locations: **{len(active_df)}**"
)

if "risk_score" in active_df.columns:

    st.sidebar.write(
        f"Average Risk: **{active_df['risk_score'].mean():.2f}**"
    )


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_locations = len(active_df)

if "risk_score" in active_df.columns:

    average_risk = active_df["risk_score"].mean()

    highest_risk = active_df["risk_score"].max()

else:

    average_risk = 0
    highest_risk = 0


if "risk_level" in active_df.columns:

    risk_levels = (
        active_df["risk_level"]
        .astype(str)
        .str.upper()
    )

    critical_count = int(
        (risk_levels == "CRITICAL").sum()
    )

    high_count = int(
        (risk_levels == "HIGH").sum()
    )

else:

    critical_count = 0
    high_count = 0

# ============================================================
# OPERATIONAL KPI CALCULATIONS
# ============================================================

if "current_incidents" in active_df.columns:

    active_incidents = int(
        (active_df["current_incidents"] > 0).sum()
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

if "traffic_density" in active_df.columns:

    average_density = active_df["traffic_density"].mean()

    maximum_density = active_df["traffic_density"].max()

else:

    average_density = 0
    maximum_density = 0


if "peak_activity" in df.columns:

    average_peak_activity = active_df["peak_activity"].mean()

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

if "risk_level" in active_df.columns:

    risk_distribution = (
        active_df["risk_level"]
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
    "risk_score" in active_df.columns
    and "location" in active_df.columns
):

    # --------------------------------------------------------
    # Calculate AI deployment using the sidebar police slider
    # --------------------------------------------------------

    highest_risk_deployment = recommend_deployment(
        active_df,
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

    center_lat = active_df["latitude"].mean()

    center_lon = active_df["longitude"].mean()

    traffic_map = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=11
    )

    # Use simulated traffic data when an incident simulation exists.
    # Otherwise use the original dataset.
    map_df = active_df

    # Use the official police decision on the map.
    if st.session_state.get("official_deployment") is not None:

        map_deployment = st.session_state[
            "official_deployment"
        ].copy()

    else:

        map_deployment = recommend_deployment(
            map_df,
            available_officers
        )

    deployment_lookup = (
        map_deployment
        .set_index("location")["recommended_officers"]
        .to_dict()
    )

    for _, row in active_df.iterrows():

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

        recommended_police = int(
            deployment_lookup.get(
                location_name,
                0
            )
        )

        popup_html = f"""
        <b>{location_name}</b><br>
        Risk Score: {risk:.2f}<br>
        Risk Level: {risk_level}<br>
        🚓 AI Recommended Deployment: {recommended_police}
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
        active_df["location"].tolist(),
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

                    # =================================================
                    # FORCE DASHBOARD REFRESH
                    # =================================================
                    # The simulation updates session state after
                    # active_df was initially created. Force a full
                    # Streamlit rerun so every dashboard section
                    # reads the new simulated dataframe.
                    st.rerun()

                    # Restart the app immediately so every dashboard
                    # section uses the simulated traffic state.
                    st.rerun()

                    st.session_state[
                        "before_row"
                    ] = before_row.to_dict()

                    # Re-run the entire dashboard so every
                    # section uses the simulated traffic state.
                    st.rerun()

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
            "after_row",
            "official_deployment",
            "official_decision",
            "official_modify_location",
            "official_modified_officers"
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
# POLICE OFFICIAL DECISION STATE
# ============================================================

if "official_deployment" not in st.session_state:
    st.session_state["official_deployment"] = None

if "official_decision" not in st.session_state:
    st.session_state["official_decision"] = "PENDING"


# ============================================================
# DEPLOYMENT CALCULATION
# ============================================================

deployment_columns_available = all(
    column in active_df.columns
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
            active_df,
            available_officers
        )

        # ----------------------------------------------------
        # POLICE OFFICIAL DECISION CONTROLS
        # ----------------------------------------------------

        st.subheader("👮 Police Official Decision")

        st.info(
            "The AI recommendation is advisory. "
            "A police official can accept, modify, or reject "
            "the recommendation. The official decision will "
            "be reflected throughout the dashboard."
        )

        decision_col1, decision_col2, decision_col3 = st.columns(3)

        with decision_col1:

            if st.button(
                "✅ Accept AI Recommendation",
                key="accept_ai_recommendation",
                use_container_width=True
            ):

                st.session_state["official_deployment"] = (
                    deployment_result.copy()
                )

                st.session_state["official_decision"] = "ACCEPTED"

                st.rerun()

        with decision_col2:

            if st.button(
                "✏️ Modify Recommendation",
                key="modify_ai_recommendation",
                use_container_width=True
            ):

                st.session_state["official_decision"] = "MODIFY"

        with decision_col3:

            if st.button(
                "❌ Reject AI Recommendation",
                key="reject_ai_recommendation",
                use_container_width=True
            ):

                rejected = deployment_result.copy()

                rejected["recommended_officers"] = 0

                st.session_state["official_deployment"] = rejected

                st.session_state["official_decision"] = "REJECTED"

                st.rerun()


        # ----------------------------------------------------
        # MODIFY AI RECOMMENDATION
        # ----------------------------------------------------

        if st.session_state.get(
            "official_decision"
        ) == "MODIFY":

            st.markdown("### ✏️ Modify AI Deployment")

            modify_location = st.selectbox(
                "Select location to modify",
                deployment_result["location"].astype(str).tolist(),
                key="official_modify_location"
            )

            selected_ai_row = deployment_result[
                deployment_result["location"].astype(str)
                == str(modify_location)
            ]

            if not selected_ai_row.empty:

                selected_ai_value = int(
                    selected_ai_row.iloc[0][
                        "recommended_officers"
                    ]
                )

            else:

                selected_ai_value = 0

            # Current official allocation excluding the
            # location currently being modified.
            current_official_total = 0

            if st.session_state.get(
                "official_deployment"
            ) is not None:

                official_current = (
                    st.session_state[
                        "official_deployment"
                    ]
                    .copy()
                )

                official_current = official_current[
                    official_current["location"].astype(str)
                    != str(modify_location)
                ]

                current_official_total = int(
                    official_current[
                        "recommended_officers"
                    ].sum()
                )

            else:

                other_locations = deployment_result[
                    deployment_result["location"].astype(str)
                    != str(modify_location)
                ]

                current_official_total = int(
                    other_locations[
                        "recommended_officers"
                    ].sum()
                )

            # Officers that can still be assigned to the
            # selected location without exceeding the pool.
            remaining_for_location = max(
                int(available_officers)
                - current_official_total,
                0
            )

            st.caption(
                f"Available Traffic Police: "
                f"{int(available_officers)} | "
                f"Already allocated elsewhere: "
                f"{current_official_total} | "
                f"Maximum allowed here: "
                f"{remaining_for_location}"
            )

            modified_officers = st.number_input(
                "Police officers to deploy",
                min_value=0,
                max_value=remaining_for_location,
                value=min(
                    selected_ai_value,
                    remaining_for_location
                ),
                step=1,
                key="official_modified_officers"
            )

            if st.button(
                "💾 Apply Official Modification",
                key="apply_official_modification",
                use_container_width=True
            ):

                official_df = deployment_result.copy()

                official_df["recommended_officers"] = (
                    official_df["recommended_officers"]
                    .astype(int)
                )

                official_df.loc[
                    official_df["location"].astype(str)
                    == str(modify_location),
                    "recommended_officers"
                ] = int(modified_officers)

                # FINAL SAFETY CHECK:
                # Total deployment must NEVER exceed the
                # available traffic police pool.
                official_total = int(
                    official_df[
                        "recommended_officers"
                    ].sum()
                )

                if official_total > int(
                    available_officers
                ):

                    st.error(
                        f"❌ Invalid deployment: "
                        f"{official_total} officers were requested, "
                        f"but only {available_officers} "
                        f"are available."
                    )

                    st.stop()

                # Store only a valid official deployment.
                st.session_state[
                    "official_deployment"
                ] = official_df

                st.session_state[
                    "official_total_deployment"
                ] = official_total

                st.session_state[
                    "official_decision"
                ] = "MODIFIED"

                st.rerun()


        # ----------------------------------------------------
        # USE OFFICIAL DECISION EVERYWHERE
        # ----------------------------------------------------

        if (
            st.session_state.get(
                "official_deployment"
            ) is not None
        ):

            deployment_result = (
                st.session_state[
                    "official_deployment"
                ].copy()
            )

            # Global safety rule:
            # Available Traffic Police must always be >=
            # total recommended deployment.
            official_total = int(
                deployment_result[
                    "recommended_officers"
                ].sum()
            )

            if official_total > int(
                available_officers
            ):

                st.error(
                    f"❌ Deployment exceeds available police: "
                    f"{official_total} recommended vs "
                    f"{available_officers} available."
                )

                # Automatically cap the allocation to the
                # available police pool.
                deployment_result[
                    "recommended_officers"
                ] = deployment_result[
                    "recommended_officers"
                ].astype(int)

                remaining_pool = int(
                    available_officers
                )

                for idx in deployment_result.index:

                    allocation = min(
                        int(
                            deployment_result.loc[
                                idx,
                                "recommended_officers"
                            ]
                        ),
                        remaining_pool
                    )

                    deployment_result.loc[
                        idx,
                        "recommended_officers"
                    ] = allocation

                    remaining_pool -= allocation

                st.session_state[
                    "official_deployment"
                ] = deployment_result.copy()

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
# POLICE OFFICIAL DECISION
# ============================================================

st.divider()

st.header("👮 Police Official Decision")

st.markdown(
    """
    The AI recommendation is advisory. A police official can
    accept it, modify it, or reject it. The final official
    decision becomes the active deployment used by the dashboard.
    """
)

# ------------------------------------------------------------
# Initialize official decision state
# ------------------------------------------------------------

if "official_decision" not in st.session_state:
    st.session_state["official_decision"] = "PENDING"

if "official_deployment" not in st.session_state:
    st.session_state["official_deployment"] = None


# ------------------------------------------------------------
# Use the current AI deployment as the starting recommendation
# ------------------------------------------------------------

ai_deployment_for_official = deployment_result.copy()


# ------------------------------------------------------------
# Current official status
# ------------------------------------------------------------

decision = st.session_state.get(
    "official_decision",
    "PENDING"
)

if decision == "ACCEPTED":

    st.success(
        "✅ AI recommendation ACCEPTED by Police Official."
    )

elif decision == "MODIFIED":

    st.warning(
        "✏️ AI recommendation MODIFIED by Police Official."
    )

elif decision == "REJECTED":

    st.error(
        "❌ AI recommendation REJECTED by Police Official."
    )

else:

    st.info(
        "⏳ Police Official Decision: PENDING"
    )


# ------------------------------------------------------------
# AI recommendation preview
# ------------------------------------------------------------

if (
    ai_deployment_for_official is not None
    and not ai_deployment_for_official.empty
):

    ai_total = int(
        ai_deployment_for_official[
            "recommended_officers"
        ].sum()
    )

    st.metric(
        "🤖 AI Recommended Deployment",
        f"{ai_total} officers"
    )

    st.metric(
        "👮 Available Traffic Police",
        int(available_officers)
    )


# ============================================================
# ACCEPT
# ============================================================

accept_col, modify_col, reject_col = st.columns(3)

with accept_col:

    if st.button(
        "✅ Accept AI Recommendation",
        key="official_accept_button",
        width="stretch"
    ):

        accepted_df = ai_deployment_for_official.copy()

        accepted_total = int(
            accepted_df[
                "recommended_officers"
            ].sum()
        )

        # Safety rule
        if accepted_total > int(
            available_officers
        ):

            st.error(
                f"Cannot accept deployment of "
                f"{accepted_total} officers. "
                f"Only {available_officers} are available."
            )

        else:

            st.session_state[
                "official_deployment"
            ] = accepted_df

            st.session_state[
                "official_decision"
            ] = "ACCEPTED"

            st.session_state[
                "official_total_deployment"
            ] = accepted_total

            st.rerun()


# ============================================================
# MODIFY
# ============================================================

with modify_col:

    if st.button(
        "✏️ Modify Recommendation",
        key="official_modify_button",
        width="stretch"
    ):

        st.session_state[
            "show_official_modify"
        ] = True


# ============================================================
# REJECT
# ============================================================

with reject_col:

    if st.button(
        "❌ Reject AI Recommendation",
        key="official_reject_button",
        width="stretch"
    ):

        rejected_df = ai_deployment_for_official.copy()

        rejected_df[
            "recommended_officers"
        ] = 0

        st.session_state[
            "official_deployment"
        ] = rejected_df

        st.session_state[
            "official_decision"
        ] = "REJECTED"

        st.session_state[
            "official_total_deployment"
        ] = 0

        st.rerun()


# ============================================================
# OFFICIAL MODIFICATION PANEL
# ============================================================

if st.session_state.get(
    "show_official_modify",
    False
):

    st.subheader(
        "✏️ AI-Assisted Deployment Modification"
    )

    st.markdown(
        """
        The AI analyses the current deployment and identifies
        locations where officers may be released and locations
        where additional officers are more urgently required.
        """
    )

    modify_df = ai_deployment_for_official.copy()

    # ------------------------------------------------------------
    # Make sure required columns exist
    # ------------------------------------------------------------

    required_modify_columns = [
        "location",
        "priority_score",
        "risk_score",
        "risk_level",
        "police_officers",
        "recommended_officers"
    ]

    missing_modify_columns = [
        c for c in required_modify_columns
        if c not in modify_df.columns
    ]

    if missing_modify_columns:

        st.error(
            "Cannot generate AI modification suggestions. "
            f"Missing columns: {missing_modify_columns}"
        )

    else:

        # --------------------------------------------------------
        # AI priority classification
        # --------------------------------------------------------

        modify_df["risk_level"] = (
            modify_df["risk_level"]
            .astype(str)
            .str.upper()
        )

        modify_df["priority_score"] = (
            pd.to_numeric(
                modify_df["priority_score"],
                errors="coerce"
            )
            .fillna(0)
        )

        modify_df["risk_score"] = (
            pd.to_numeric(
                modify_df["risk_score"],
                errors="coerce"
            )
            .fillna(0)
        )

        modify_df["police_officers"] = (
            pd.to_numeric(
                modify_df["police_officers"],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

        modify_df["recommended_officers"] = (
            pd.to_numeric(
                modify_df["recommended_officers"],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

        # --------------------------------------------------------
        # LOW PRIORITY / RELEASE CANDIDATES
        # --------------------------------------------------------
        #
        # A location is a release candidate when:
        # - its priority is relatively low
        # - it currently has police assigned
        #
        # We use the lower half of priority scores rather than
        # blindly assuming that every MODERATE location is safe.
        # --------------------------------------------------------

        priority_median = modify_df[
            "priority_score"
        ].median()

        release_candidates = modify_df[
            (
                modify_df["priority_score"]
                <= priority_median
            )
            &
            (
                modify_df["recommended_officers"]
                > 0
            )
        ].copy()

        # --------------------------------------------------------
        # HIGH PRIORITY / RECEIVER LOCATIONS
        # --------------------------------------------------------

        receiver_candidates = modify_df[
            modify_df["recommended_officers"]
            <
            modify_df["recommended_officers"].clip(
                lower=0
            )
        ].copy()

        # The expression above is intentionally replaced below
        # with an explicit AI demand calculation.

        def calculate_ai_need(row):

            risk = float(row["risk_score"])
            level = str(row["risk_level"]).upper()
            incidents = int(
                row.get("current_incidents", 0)
            )

            if level == "CRITICAL" or risk >= 80:
                need = 3
            elif level == "HIGH" or risk >= 65:
                need = 2
            elif level == "MODERATE" or risk >= 45:
                need = 1
            else:
                need = 0

            if incidents > 0:
                need = max(need, 1)

            return need

        modify_df["AI Required Officers"] = modify_df.apply(
            calculate_ai_need,
            axis=1
        )

        modify_df["Additional Officers Needed"] = (
            modify_df["AI Required Officers"]
            -
            modify_df["recommended_officers"]
        ).clip(lower=0)

        receiver_candidates = modify_df[
            modify_df[
                "Additional Officers Needed"
            ] > 0
        ].copy()

        receiver_candidates = receiver_candidates.sort_values(
            "priority_score",
            ascending=False
        )

        release_candidates = release_candidates.sort_values(
            "priority_score",
            ascending=True
        )

        # --------------------------------------------------------
        # AI TRANSFER SUGGESTIONS
        # --------------------------------------------------------

        suggestions = []

        available_transfer_pool = 0

        for _, row in release_candidates.iterrows():

            releasable = int(
                row["recommended_officers"]
            )

            if releasable <= 0:
                continue

            suggestions.append(
                {
                    "from_location":
                        row["location"],
                    "from_priority":
                        float(row["priority_score"]),
                    "from_risk":
                        float(row["risk_score"]),
                    "available_to_release":
                        releasable
                }
            )

            available_transfer_pool += releasable

        transfers = []

        remaining_pool = available_transfer_pool

        for _, receiver in receiver_candidates.iterrows():

            if remaining_pool <= 0:
                break

            needed = int(
                receiver[
                    "Additional Officers Needed"
                ]
            )

            allocation = min(
                needed,
                remaining_pool
            )

            if allocation <= 0:
                continue

            transfers.append(
                {
                    "to_location":
                        receiver["location"],
                    "to_priority":
                        float(receiver["priority_score"]),
                    "to_risk":
                        float(receiver["risk_score"]),
                    "officers":
                        allocation
                }
            )

            remaining_pool -= allocation

        # --------------------------------------------------------
        # DISPLAY AI SUGGESTION
        # --------------------------------------------------------

        st.subheader(
            "🤖 AI Recommended Reallocation"
        )

        if transfers and suggestions:

            st.success(
                "The AI found a possible reallocation: "
                "release officers from lower-priority locations "
                "and move them to locations with greater need."
            )

            transfer_rows = []

            release_index = 0

            for transfer in transfers:

                officers_needed = transfer[
                    "officers"
                ]

                while officers_needed > 0:

                    if release_index >= len(
                        suggestions
                    ):
                        break

                    source = suggestions[
                        release_index
                    ]

                    movable = min(
                        officers_needed,
                        source[
                            "available_to_release"
                        ]
                    )

                    if movable > 0:

                        transfer_rows.append(
                            {
                                "Release From":
                                    source[
                                        "from_location"
                                    ],
                                "Source Priority":
                                    round(
                                        source[
                                            "from_priority"
                                        ],
                                        2
                                    ),
                                "Source Risk":
                                    round(
                                        source[
                                            "from_risk"
                                        ],
                                        2
                                    ),
                                "Move Officers":
                                    movable,
                                "Reallocate To":
                                    transfer[
                                        "to_location"
                                    ],
                                "Destination Priority":
                                    round(
                                        transfer[
                                            "to_priority"
                                        ],
                                        2
                                    ),
                                "Destination Risk":
                                    round(
                                        transfer[
                                            "to_risk"
                                        ],
                                        2
                                    )
                            }
                        )

                        suggestions[
                            release_index
                        ][
                            "available_to_release"
                        ] -= movable

                        officers_needed -= movable

                    if suggestions[
                        release_index
                    ][
                        "available_to_release"
                    ] <= 0:

                        release_index += 1

            if transfer_rows:

                transfer_df = pd.DataFrame(
                    transfer_rows
                )

                st.dataframe(
                    transfer_df,
                    width="stretch",
                    hide_index=True
                )

                total_transfer = int(
                    transfer_df[
                        "Move Officers"
                    ].sum()
                )

                st.info(
                    f"💡 AI suggests moving "
                    f"**{total_transfer} officer(s)** "
                    f"from lower-priority locations to "
                    f"higher-priority locations."
                )

            else:

                st.info(
                    "No safe officer reallocation was identified."
                )

        else:

            st.info(
                "No low-priority officer allocation can "
                "currently be released for a higher-priority "
                "location."
            )

        # --------------------------------------------------------
        # MANUAL OFFICIAL MODIFICATION
        # --------------------------------------------------------

        st.subheader(
            "✏️ Official Modification"
        )

        st.caption(
            "The AI suggestion is advisory. "
            "The police official makes the final decision."
        )

        modify_locations = (
            modify_df["location"]
            .astype(str)
            .tolist()
        )

        modify_location = st.selectbox(
            "Select location to modify",
            modify_locations,
            key="official_modify_location"
        )

        selected_row = modify_df[
            modify_df["location"].astype(str)
            == str(modify_location)
        ].iloc[0]

        current_allocation = int(
            selected_row[
                "recommended_officers"
            ]
        )

        # --------------------------------------------------------
        # Calculate maximum legal allocation
        # --------------------------------------------------------

        other_locations = modify_df[
            modify_df["location"].astype(str)
            != str(modify_location)
        ]

        officers_elsewhere = int(
            other_locations[
                "recommended_officers"
            ].sum()
        )

        maximum_allowed = max(
            int(available_officers)
            - officers_elsewhere,
            0
        )

        st.write(
            f"Current AI allocation: "
            f"**{current_allocation} officers**"
        )

        st.write(
            f"Maximum allowed after considering "
            f"other locations: "
            f"**{maximum_allowed} officers**"
        )

        modified_officers = st.number_input(
            "Final officers at selected location",
            min_value=0,
            max_value=maximum_allowed,
            value=min(
                current_allocation,
                maximum_allowed
            ),
            step=1,
            key="official_modified_officers"
        )

        save_col, cancel_col = st.columns(2)

        with save_col:

            if st.button(
                "💾 Save Official Modification",
                key="save_official_modification",
                width="stretch"
            ):

                modified_df = modify_df.copy()

                modified_df.loc[
                    modified_df[
                        "location"
                    ].astype(str)
                    == str(modify_location),
                    "recommended_officers"
                ] = int(modified_officers)

                # ------------------------------------------------
                # HARD AVAILABLE-OFFICER VALIDATION
                # ------------------------------------------------

                final_total = int(
                    modified_df[
                        "recommended_officers"
                    ].sum()
                )

                if final_total > int(
                    available_officers
                ):

                    st.error(
                        f"❌ Invalid decision: "
                        f"{final_total} officers requested, "
                        f"but only {available_officers} "
                        f"are available."
                    )

                else:

                    st.session_state[
                        "official_deployment"
                    ] = modified_df

                    st.session_state[
                        "official_decision"
                    ] = "MODIFIED"

                    st.session_state[
                        "official_total_deployment"
                    ] = final_total

                    st.session_state[
                        "show_official_modify"
                    ] = False

                    st.rerun()

        with cancel_col:

            if st.button(
                "Cancel",
                key="cancel_official_modification",
                width="stretch"
            ):

                st.session_state[
                    "show_official_modify"
                ] = False

                st.rerun()



# ============================================================
# FINAL OFFICIAL DEPLOYMENT
# ============================================================

official_deployment = st.session_state.get(
    "official_deployment"
)

if (
    official_deployment is not None
    and not official_deployment.empty
):

    final_total = int(
        official_deployment[
            "recommended_officers"
        ].sum()
    )

    st.subheader(
        "📋 Final Official Deployment"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "👮 Available Police",
            int(available_officers)
        )

    with col2:

        st.metric(
            "🚓 Final Deployment",
            final_total
        )

    with col3:

        st.metric(
            "🟢 Remaining Police",
            max(
                int(available_officers)
                - final_total,
                0
            )
        )

    final_columns = [
        column
        for column in [
            "location",
            "risk_score",
            "risk_level",
            "priority_score",
            "recommended_officers"
        ]
        if column in official_deployment.columns
    ]

    final_display = official_deployment[
        final_columns
    ].rename(
        columns={
            "recommended_officers":
                "Final Official Deployment"
        }
    )

    st.dataframe(
        final_display,
        width="stretch",
        hide_index=True
    )


# ============================================================
# AI PRIORITY ORDER
# ============================================================

# All locations are ranked by the AI priority score.
# Highest priority appears first.
#
# No Top-10 limitation is used.

if (
    deployment_result is not None
    and not deployment_result.empty
    and "priority_score" in deployment_result.columns
):

    deployment_result = (
        deployment_result
        .sort_values(
            "priority_score",
            ascending=False
        )
        .reset_index(drop=True)
    )

    deployment_result["AI Priority Rank"] = (
        range(1, len(deployment_result) + 1)
    )

    deployment_result["AI Priority"] = (
        deployment_result["priority_score"]
        .astype(float)
        .round(2)
    )

    deployment_result["Priority Category"] = (
        deployment_result["risk_level"]
        .astype(str)
        .str.upper()
        .map(
            lambda level:
                "🔴 CRITICAL AI PRIORITY"
                if level == "CRITICAL"
                else
                "🟠 HIGH AI PRIORITY"
                if level == "HIGH"
                else
                "🟢 MODERATE AI PRIORITY"
                if level == "MODERATE"
                else
                "🔵 LOW AI PRIORITY"
        )
    )

    st.subheader(
        "📊 All Locations — AI Priority Ranking"
    )

    st.caption(
        "All locations are ranked by AI Priority Score, "
        "from highest priority to lowest priority."
    )

    priority_display_columns = [
        column
        for column in [
            "AI Priority Rank",
            "location",
            "AI Priority",
            "Priority Category",
            "risk_score",
            "risk_level",
            "recommended_officers"
        ]
        if column in deployment_result.columns
    ]

    priority_display = deployment_result[
        priority_display_columns
    ].rename(
        columns={
            "location": "Location",
            "risk_score": "Traffic Risk Score",
            "risk_level": "Risk Level",
            "recommended_officers":
                "AI Recommended Officers"
        }
    )

    st.dataframe(
        priority_display,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # Highest priority location
    # --------------------------------------------------------

    highest_priority = deployment_result.iloc[0]

    st.info(
        f"🎯 **Highest AI Priority:** "
        f"{highest_priority['location']} "
        f"— AI Priority Score: "
        f"**{float(highest_priority['priority_score']):.2f}**"
    )

else:

    st.warning(
        "AI priority ranking is not available."
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
