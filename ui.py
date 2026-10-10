import streamlit as st
import cv2
import time
import os
import tempfile
import pandas as pd
import plotly.express as px
from detector import ObjectDetector
from database import DatabaseManager
import config

CYBERPUNK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --cp-yellow: #FCEE0A;
    --cp-cyan: #00F0FF;
    --cp-red: #FF003C;
    --cp-green: #00FF9D;
    --cp-purple: #9D00FF;
    --cp-black: #050508;
    --cp-dark: #090a10;
    --cp-panel: #0e101a;
    --cp-panel-border: #1a1e30;
    --cp-muted: #8b92a5;
}

/* Global Application Styling */
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Rajdhani', sans-serif !important;
}

.stApp {
    background-color: var(--cp-black) !important;
    color: #e5e7eb !important;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(0, 240, 255, 0.03) 0%, transparent 20%),
        radial-gradient(circle at 90% 80%, rgba(252, 238, 10, 0.03) 0%, transparent 20%),
        linear-gradient(rgba(14, 16, 26, 0.5) 1px, transparent 1px),
        linear-gradient(90deg, rgba(14, 16, 26, 0.5) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
}

/* Top Header Bar */
[data-testid="stHeader"] {
    background: rgba(5, 5, 8, 0.95) !important;
    border-bottom: 1px solid var(--cp-panel-border) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #08090f !important;
    border-right: 2px solid var(--cp-yellow) !important;
    box-shadow: 4px 0 25px rgba(252, 238, 10, 0.08);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

/* Headings */
h1, h2, h3, h4 {
    font-family: 'Orbitron', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 2px !important;
}

h1 {
    color: var(--cp-yellow) !important;
    font-weight: 900 !important;
    text-shadow: 0 0 20px rgba(252, 238, 10, 0.45);
}

h2 {
    color: var(--cp-cyan) !important;
    text-shadow: 0 0 15px rgba(0, 240, 255, 0.35);
}

h3 {
    color: var(--cp-yellow) !important;
    font-size: 1.15rem !important;
}

/* Cyber Banner & Ticker */
.cyber-ticker {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 0, 60, 0.12);
    border: 1px solid var(--cp-red);
    padding: 7px 16px;
    margin-bottom: 18px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    color: var(--cp-yellow);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    box-shadow: 0 0 12px rgba(255, 0, 60, 0.2);
}

.cyber-header-box {
    display: flex;
    align-items: center;
    gap: 20px;
    background: linear-gradient(135deg, rgba(14, 16, 26, 0.95), rgba(9, 10, 16, 0.9));
    border: 1px solid var(--cp-panel-border);
    border-left: 5px solid var(--cp-yellow);
    border-right: 2px solid var(--cp-cyan);
    padding: 20px 24px;
    margin-bottom: 24px;
    clip-path: polygon(0 0, calc(100% - 18px) 0, 100% 18px, 100% 100%, 18px 100%, 0 calc(100% - 18px));
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.6);
}

.cyber-logo-badge {
    width: 68px;
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--cp-yellow);
    color: #050508;
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 28px;
    clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px));
    box-shadow: 0 0 25px rgba(252, 238, 10, 0.4);
}

.cyber-title-text {
    font-family: 'Orbitron', sans-serif;
    font-size: clamp(22px, 3.2vw, 36px);
    font-weight: 900;
    color: var(--cp-yellow);
    line-height: 1.1;
    letter-spacing: 2.5px;
    text-shadow: 0 0 16px rgba(252, 238, 10, 0.4);
}

.cyber-title-text span {
    color: var(--cp-red);
    text-shadow: 0 0 16px rgba(255, 0, 60, 0.6);
}

.cyber-subtitle-text {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    color: var(--cp-cyan);
    letter-spacing: 1.5px;
    margin-top: 6px;
}

.cyber-creator-tag {
    display: inline-block;
    background: rgba(0, 240, 255, 0.1);
    border: 1px solid var(--cp-cyan);
    color: var(--cp-cyan);
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px;
    padding: 3px 12px;
    margin-top: 8px;
    letter-spacing: 1.5px;
}

/* Metric Cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0e101a 0%, #08090f 100%) !important;
    border: 1px solid #1a1e30 !important;
    border-left: 4px solid var(--cp-yellow) !important;
    border-bottom: 2px solid var(--cp-cyan) !important;
    padding: 14px 18px !important;
    clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px)) !important;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.5) !important;
}

div[data-testid="stMetric"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 1.5px !important;
    color: #9ca3af !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--cp-yellow) !important;
    text-shadow: 0 0 12px rgba(252, 238, 10, 0.4) !important;
}

/* Buttons */
button[kind="primary"] {
    background: var(--cp-yellow) !important;
    color: #050508 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 0px !important;
    clip-path: polygon(10px 0, 100% 0, calc(100% - 10px) 100%, 0 100%) !important;
    box-shadow: 0 0 20px rgba(252, 238, 10, 0.4) !important;
    transition: all 0.2s ease-in-out !important;
}

button[kind="primary"]:hover {
    background: #ffffff !important;
    box-shadow: 0 0 28px rgba(255, 255, 255, 0.8) !important;
    transform: translateY(-1px) !important;
}

button[kind="secondary"] {
    background: rgba(255, 0, 60, 0.12) !important;
    color: var(--cp-red) !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    border: 1px solid var(--cp-red) !important;
    border-radius: 0px !important;
    clip-path: polygon(10px 0, 100% 0, calc(100% - 10px) 100%, 0 100%) !important;
    box-shadow: 0 0 12px rgba(255, 0, 60, 0.3) !important;
    transition: all 0.2s ease-in-out !important;
}

button[kind="secondary"]:hover {
    background: var(--cp-red) !important;
    color: #ffffff !important;
    box-shadow: 0 0 24px rgba(255, 0, 60, 0.7) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #090a10 !important;
    border-bottom: 2px solid var(--cp-panel-border) !important;
    gap: 10px !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #8b92a5 !important;
    padding: 12px 22px !important;
    border-radius: 0px !important;
    border: 1px solid transparent !important;
}

.stTabs [aria-selected="true"] {
    color: var(--cp-yellow) !important;
    border-bottom: 3px solid var(--cp-yellow) !important;
    background: rgba(252, 238, 10, 0.05) !important;
    text-shadow: 0 0 10px rgba(252, 238, 10, 0.4) !important;
}

/* Status Dot Indicators */
.hud-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
}

.hud-dot.green { background: #00FF9D; box-shadow: 0 0 10px #00FF9D; }
.hud-dot.yellow { background: #FCEE0A; box-shadow: 0 0 10px #FCEE0A; }
.hud-dot.red { background: #FF003C; box-shadow: 0 0 10px #FF003C; }
.hud-dot.cyan { background: #00F0FF; box-shadow: 0 0 10px #00F0FF; }

/* Code & Monospace font */
code, .font-mono {
    font-family: 'Share Tech Mono', monospace !important;
}

/* Streamlit dataframes */
.stDataFrame {
    border: 1px solid #1a1e30 !important;
}

/* Custom scrollbars */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #050508; }
::-webkit-scrollbar-thumb { background: var(--cp-yellow); }

footer { visibility: hidden; }
</style>
"""

CYBER_PALETTE = ['#FCEE0A', '#00F0FF', '#FF003C', '#00FF9D', '#BF00FF', '#FF7700']

def get_cyber_plot_layout():
    return dict(
        paper_bgcolor='rgba(14, 16, 26, 0.95)',
        plot_bgcolor='rgba(14, 16, 26, 0.95)',
        font=dict(family='Share Tech Mono, monospace', color='#FCEE0A', size=12),
        xaxis=dict(
            gridcolor='#1A1E30',
            zerolinecolor='#1A1E30',
            color='#00F0FF',
            tickfont=dict(family='Share Tech Mono, monospace')
        ),
        yaxis=dict(
            gridcolor='#1A1E30',
            zerolinecolor='#1A1E30',
            color='#00F0FF',
            tickfont=dict(family='Share Tech Mono, monospace')
        ),
        colorway=CYBER_PALETTE
    )

def render_dashboard():
    st.set_page_config(
        page_title="NIGHT CITY // VISION OPS 2077",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject Cyberpunk 2077 Styles
    st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

    # Night City HUD Banner & Header
    st.markdown("""
    <div class="cyber-ticker">
        <span>● NIGHT CITY // SECTOR 04 OPTICAL SUBNET ACTIVE</span>
        <span>SECURITY PROTOCOL: ARASAKA CORP-DEFENSE</span>
        <span>HUD ENGINE // BUILD 2.077</span>
    </div>
    <div class="cyber-header-box">
        <div class="cyber-logo-badge">V/</div>
        <div>
            <div class="cyber-title-text">VISION OPS <span>2077</span></div>
            <div class="cyber-subtitle-text">AUTONOMOUS OPTICAL TARGETING GRID // YOLOv8 × OPENCV × RELATIONAL DB</div>
            <div class="cyber-creator-tag">OPERATOR: AKASH // PROTOCOL STATUS: ENGAGED</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize components in session state
    if 'detector' not in st.session_state:
        st.session_state.detector = ObjectDetector(config.DEFAULT_MODEL)
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager(use_sqlite_fallback=True)
    if 'is_detecting' not in st.session_state:
        st.session_state.is_detecting = False
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None

    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ SYSTEM CONFIG")

        # Database Fallback Setting
        use_fallback = st.checkbox(
            "ENABLE LOCAL SQLITE FALLBACK",
            value=st.session_state.db.use_sqlite_fallback,
            help="If MySQL server is offline, saves detection telemetry to local SQLite storage (detection_logs.db)."
        )
        st.session_state.db.use_sqlite_fallback = use_fallback

        # Check / Ensure Database Connection
        db_status = st.session_state.db.connect()
        active_backend = st.session_state.db.get_backend()

        # Telemetry Status
        st.subheader("GRID STATUS")
        if db_status:
            if active_backend == "mysql":
                st.markdown(f'<span class="hud-dot green"></span><strong>MYSQL ACTIVE</strong> <code style="color:#00F0FF">[{config.DB_NAME}]</code>', unsafe_allow_html=True)
            elif active_backend == "sqlite":
                st.markdown('<span class="hud-dot cyan"></span><strong>SQLITE ACTIVE</strong> <code style="color:#FCEE0A">[detection_logs.db]</code>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="hud-dot red"></span><strong>DATABASE OFFLINE</strong>', unsafe_allow_html=True)
            st.caption("Tip: Start MySQL service (`Start-Service MySQL80`) or enable SQLite Fallback.")

        if st.session_state.detector.is_model_loaded():
            st.markdown('<span class="hud-dot yellow"></span><strong>YOLOv8n KIROSHI OPTICS LOADED</strong>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="hud-dot red"></span><strong>NEURAL ENGINE FAILURE</strong>', unsafe_allow_html=True)

        st.markdown("---")

        # Detection Controls
        st.subheader("TARGETING PARAMS")
        conf_threshold = st.slider("CONFIDENCE THRESHOLD", 0.10, 0.95, float(config.CONFIDENCE_THRESHOLD), 0.05)

        classes_options = ["All"] + config.COCO_CLASSES
        selected_classes = st.multiselect("CLASSIFICATION FILTER", options=classes_options, default=["All"])

        source_options = ["Sample Demo Video", "Webcam", "Video File"]
        source = st.selectbox("OPTICAL INPUT SOURCE", source_options, index=0)

        video_file = None
        if source == "Video File":
            video_file = st.file_uploader("UPLOAD FEED FILE", type=['mp4', 'avi', 'mov', 'mkv'])

        enable_logging = st.checkbox("TELEMETRY LOGGING", value=True)
        log_interval = st.number_input(
            "LOG INTERVAL (FRAMES)",
            min_value=1,
            max_value=300,
            value=10,
            help="Log detection telemetry every N frames."
        )

        st.markdown("---")

        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("▶ ENGAGE", type="primary", use_container_width=True):
                st.session_state.error_message = None
                if source == "Video File" and video_file is None:
                    st.session_state.error_message = "No video stream uploaded. Provide file before engaging."
                else:
                    st.session_state.is_detecting = True
        with col_stop:
            if st.button("⏹ DISENGAGE", type="secondary", use_container_width=True):
                st.session_state.is_detecting = False

    # --- Main Content Tabs ---
    tab1, tab2, tab3 = st.tabs(["◈ LIVE HUD FEED & KPIS", "◈ TELEMETRY ARCHIVE", "◈ NEURAL ANALYTICS"])

    # Tab 1: Live Feed & Metrics
    with tab1:
        if st.session_state.error_message:
            st.error(f"⚠️ {st.session_state.error_message}")
            if st.button("DISMISS ALERT"):
                st.session_state.error_message = None
                st.rerun()

        frame_placeholder = st.empty()
        metrics_placeholder = st.empty()

        if not st.session_state.is_detecting:
            frame_placeholder.markdown(f"""
            <div style="background:#0e101a; border:1px solid #1a1e30; border-left:4px solid #FCEE0A; padding:24px; font-family:'Share Tech Mono', monospace;">
                <h4 style="color:#FCEE0A; margin-top:0;">◈ SYSTEM STANDBY // OPTICAL SCANNER IDLE</h4>
                <p style="color:#d1d5db; margin-bottom:8px;">Optical Feed Input: <span style="color:#00F0FF; font-weight:bold;">{source}</span></p>
                <p style="color:#9ca3af; margin:0;">Press <strong style="color:#FCEE0A;">▶ ENGAGE</strong> in the sidebar to activate the Kiroshi Optics target identification grid.</p>
            </div>
            """, unsafe_allow_html=True)

    # Tab 2: Telemetry Archive
    with tab2:
        col_log_header, col_log_refresh = st.columns([3, 1])
        with col_log_header:
            st.subheader("TARGET TELEMETRY RECORDS")
        with col_log_refresh:
            if st.button("🔄 RESCAN LOGS", use_container_width=True):
                st.rerun()

        if db_status:
            logs_data = st.session_state.db.get_recent_logs(limit=100)
            if logs_data:
                df_logs = pd.DataFrame(logs_data)
                st.dataframe(df_logs, width="stretch", hide_index=True)

                col_stat1, col_stat2 = st.columns([2, 1])
                with col_stat1:
                    st.caption(f"TELEMETRY STREAM: Displaying latest {len(df_logs)} target encounters.")
                with col_stat2:
                    csv_data = df_logs.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 EXPORT DATASET (CSV)",
                        data=csv_data,
                        file_name="telemetry_logs_2077.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("No targeting events recorded in database yet. Engage detection feed to populate telemetry records.")
        else:
            st.warning("Database offline. Enable SQLite fallback or initialize MySQL service to stream logs.")

    # Tab 3: Analytics & Visualizations
    with tab3:
        st.subheader("NEURAL GRID TELEMETRY CHARTS")
        if db_status:
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                counts_data = st.session_state.db.get_class_counts()
                if counts_data:
                    df_counts = pd.DataFrame(counts_data)
                    fig_bar = px.bar(
                        df_counts,
                        x='object_class',
                        y='count',
                        color='object_class',
                        title="CLASSIFICATION FREQUENCY",
                        labels={'object_class': 'OBJECT CLASS', 'count': 'TOTAL DETECTIONS'},
                        text_auto=True,
                        color_discrete_sequence=CYBER_PALETTE
                    )
                    fig_bar.update_layout(get_cyber_plot_layout())
                    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
                    st.plotly_chart(fig_bar, width="stretch")
                else:
                    st.info("Insufficient data for classification distribution chart.")

            with col_chart2:
                time_data = st.session_state.db.get_detections_over_time()
                if time_data:
                    df_time = pd.DataFrame(time_data)
                    fig_line = px.line(
                        df_time,
                        x='time_interval',
                        y='count',
                        title="TEMPORAL ACTIVITY TIMELINE",
                        labels={'time_interval': 'MINUTE INTERVAL', 'count': 'ENCOUNTERS'},
                        markers=True,
                        color_discrete_sequence=['#00F0FF']
                    )
                    fig_line.update_layout(get_cyber_plot_layout())
                    st.plotly_chart(fig_line, width="stretch")
                else:
                    st.info("Insufficient temporal data points yet. Telemetry will graph chronologically.")
        else:
            st.warning("Database offline. Re-establish connection to render intelligence dashboards.")

    # --- Video Detection Loop ---
    if st.session_state.is_detecting:
        cap = None
        temp_video_path = None

        try:
            if source == "Sample Demo Video":
                demo_video_path = os.path.join(os.path.dirname(__file__), "assets", "sample_demo.mp4")
                if os.path.exists(demo_video_path):
                    cap = cv2.VideoCapture(demo_video_path)
                else:
                    st.session_state.error_message = "Asset file missing: assets/sample_demo.mp4."
                    st.session_state.is_detecting = False
            elif source == "Webcam":
                cap = cv2.VideoCapture(0)
            elif source == "Video File":
                if video_file is not None:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(video_file.read())
                    tfile.flush()
                    tfile.close()
                    temp_video_path = tfile.name
                    cap = cv2.VideoCapture(temp_video_path)
                else:
                    st.session_state.error_message = "Feed file payload empty."
                    st.session_state.is_detecting = False

            if cap is None or not cap.isOpened():
                st.session_state.error_message = f"Optical device error: could not connect to {source}. Switch to 'Sample Demo Video' to test."
                st.session_state.is_detecting = False
                if not st.session_state.is_detecting:
                    return

            frame_count = 0
            total_objects_session = 0
            last_logged_time = {}
            prev_time = time.time()

            # Render immediate disengage button in Tab 1
            with tab1:
                if st.button("⏹ DISENGAGE FEED", key="tab_stop_btn", type="secondary"):
                    st.session_state.is_detecting = False

            while st.session_state.is_detecting:
                ret, frame = cap.read()
                if not ret:
                    if source == "Sample Demo Video":
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        st.info("Optical feed stream finished.")
                        st.session_state.is_detecting = False
                        break

                frame_count += 1

                # Convert BGR to RGB for Streamlit rendering
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Process frame with YOLO detector (Kiroshi Optics HUD boxes)
                processed_frame, detections = st.session_state.detector.process_frame(
                    frame_rgb,
                    conf_threshold=conf_threshold,
                    selected_classes=selected_classes
                )

                # Calculate Processing FPS
                curr_time = time.time()
                time_diff = curr_time - prev_time
                fps = 1.0 / time_diff if time_diff > 0 else 0.0
                prev_time = curr_time

                # Metrics calculations
                current_objects = len(detections)
                total_objects_session += current_objects
                avg_conf = (sum([d['confidence'] for d in detections]) / current_objects) if current_objects > 0 else 0.0

                # Database Logging
                if enable_logging and db_status and (frame_count % log_interval == 0):
                    curr_t = time.time()
                    for d in detections:
                        cls = d['class_name']
                        if curr_t - last_logged_time.get(cls, 0) > 0.5:
                            st.session_state.db.log_detection(
                                cls, d['confidence'],
                                d['bbox_x'], d['bbox_y'], d['bbox_w'], d['bbox_h']
                            )
                            last_logged_time[cls] = curr_t

                # Display processed frame
                frame_placeholder.image(processed_frame, channels="RGB", width="stretch")

                # Display KPI metrics
                with metrics_placeholder.container():
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("TARGETS IN FRAME", current_objects)
                    m2.metric("OPTICAL FPS", f"{fps:.1f}")
                    m3.metric("AVG CONFIDENCE", f"{avg_conf:.1%}")
                    m4.metric("TOTAL DETECTIONS", total_objects_session)

                # Small delay to keep UI smooth
                time.sleep(0.01)

        finally:
            if cap is not None:
                cap.release()
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception:
                    pass
