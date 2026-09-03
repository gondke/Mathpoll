import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import string
import io

# ==========================================
# 1. PAGE CONFIGURATION & STYLING (Dark / High Contrast)
# ==========================================
st.set_page_config(
    page_title="MathPhys Chem Real-Time Polling",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast CSS with MathJax integration
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* High contrast cards */
    .metric-card {
        background-color: #1F2937;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    .question-box {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }

    /* Primary Accent Buttons */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3B82F6;
        box-shadow: 0 0 10px #3B82F6;
    }
</style>

<!-- Load MathJax for TeX Rendering -->
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if "quiz_code" not in st.session_state:
    st.session_state.quiz_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
if "students_df" not in st.session_state:
    st.session_state.students_df = None
if "groups" not in st.session_state:
    st.session_state.groups = {}
if "responses" not in st.session_state:
    st.session_state.responses = []

# Sample initial physics/math/chemistry MCQ
if "question" not in st.session_state:
    st.session_state.question = r"Solve the Schrödinger Equation eigenvalue problem for $\psi(x)$ where $\hat{H} = -\frac{\hbar^2}{2m}\nabla^2 + V(x)$:"
if "options" not in st.session_state:
    st.session_state.options = [
        r"$E \psi(x)$",
        r"$\frac{d}{dx}\psi(x)$",
        r"$\int_0^\infty \psi(x) dx$",
        r"$\hbar \omega$"
    ]

# ==========================================
# 3. SIDEBAR: QUIZ CONTROL & GROUP SETUP
# ==========================================
st.sidebar.title("⚛️ Teacher Controls")

# Session Code Display
st.sidebar.markdown(f"""
<div class="metric-card">
    <span style="color: #9CA3AF; font-size: 0.9em;">Session OTP / Code</span><br>
    <span style="color: #60A5FA; font-weight: bold; font-size: 2em; letter-spacing: 3px;">{st.session_state.quiz_code}</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("1. Student & Group Roster")

# Student Data Input
upload_option = st.sidebar.radio("Input Student Roster", ["Generate Sample Data (100 Students)", "Upload CSV File"])

if upload_option == "Generate Sample Data (100 Students)":
    if st.sidebar.button("Generate Roster"):
        data = {
            "Roll_No": [f"2026_STEM_{i:03d}" for i in range(1, 101)],
            "Name": [f"Student_{i}" for i in range(1, 101)]
        }
        st.session_state.students_df = pd.DataFrame(data)
        st.sidebar.success("Generated 100 student records!")

else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Columns: Roll_No, Name)", type=["csv"])
    if uploaded_file:
        st.session_state.students_df = pd.read_csv(uploaded_file)
        st.sidebar.success("Roster Uploaded Successfully!")

# Grouping Logic
if st.session_state.students_df is not None:
    group_method = st.sidebar.selectbox("Grouping Strategy", ["Auto-Divide into N Groups", "Manual Group Assignment"])
    
    num_groups = st.sidebar.number_input("Number of Groups", min_value=2, max_value=10, value=4)
    
    if st.sidebar.button("Form Groups"):
        df = st.session_state.students_df.copy()
        if group_method == "Auto-Divide into N Groups":
            df = df.sample(frac=1).reset_index(drop=True)  # Shuffle students randomly
            st.session_state.groups = {}
            for i in range(num_groups):
                group_name = f"Group {chr(65 + i)}"  # Group A, Group B, Group C...
                st.session_state.groups[group_name] = df.iloc[i::num_groups]["Roll_No"].tolist()
            st.sidebar.success(f"Divided {len(df)} students into {num_groups} groups!")

st.sidebar.markdown("---")
st.sidebar.subheader("2. Chart Configuration")
chart_type = st.sidebar.selectbox("Visualization Type", ["Bar Chart (Histogram)", "Pie Chart", "Group Stacked Bar Chart"])

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🧪 STEM Live Real-Time Polling System")

# TeX Question Editor (Teacher Area)
with st.expander("📝 Question & LaTeX Editor", expanded=False):
    st.session_state.question = st.text_input("Enter Question (LaTeX supported via $...$):", value=st.session_state.question)
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.options[0] = st.text_input("Option A", value=st.session_state.options[0])
        st.session_state.options[1] = st.text_input("Option B", value=st.session_state.options[1])
    with col_b:
        st.session_state.options[2] = st.text_input("Option C", value=st.session_state.options[2])
        st.session_state.options[3] = st.text_input("Option D", value=st.session_state.options[3])

# Question Display Card
st.markdown(f"""
<div class="question-box">
    <h3 style="color:#F3F4F6; margin-top:0;">Current Question:</h3>
    <p style="font-size: 1.3em; color: #E0E7FF;">{st.session_state.question}</p>
</div>
""", unsafe_allow_html=True)

# Main Grid Layout: Student Portal (Left) | Live Analytics (Right)
col_student, col_analytics = st.columns([1, 1.2])

# ------------------------------------------
# STUDENT SIMULATOR / INTERFACE (Left Column)
# ------------------------------------------
with col_student:
    st.subheader("📲 Student Response Portal")
    
    # Input Roll No
    student_roll = st.text_input("Enter Your Roll Number:", value="2026_STEM_001")
    
    # Identify student group
    assigned_group = "Unassigned"
    for grp, members in st.session_state.groups.items():
        if student_roll in members:
            assigned_group = grp
            break
            
    st.info(f"**Assigned Group:** {assigned_group}")
    
    # Option Selection with TeX
    selected_option = st.radio("Select the correct mathematical identity:", st.session_state.options)
    
    if st.button("Submit Answer 🚀"):
        if assigned_group == "Unassigned":
            st.error("Please form groups in the sidebar first!")
        else:
            # Append response to live state
            st.session_state.responses.append({
                "Roll_No": student_roll,
                "Group": assigned_group,
                "Option": selected_option
            })
            st.success("Response recorded in real-time!")

    st.markdown("---")
    # Quick Simulation Tool for Live Demo
    if st.button("⚡ Simulate Random Class Responses (80 Students)"):
        if not st.session_state.groups:
            st.warning("Please setup groups first!")
        else:
            st.session_state.responses = []
            for grp, members in st.session_state.groups.items():
                for student in members:
                    st.session_state.responses.append({
                        "Roll_No": student,
                        "Group": grp,
                        "Option": random.choice(st.session_state.options)
                    })
            st.rerun()

# ------------------------------------------
# LIVE ANALYTICS & CHARTS (Right Column)
# ------------------------------------------
with col_analytics:
    st.subheader("📊 Live Poll Analytics")
    
    if len(st.session_state.responses) == 0:
        st.warning("Awaiting live responses from students...")
    else:
        df_resp = pd.DataFrame(st.session_state.responses)
        
        # Total votes counter
        st.metric(label="Total Live Responses Received", value=len(df_resp))
        
        # Plotting based on teacher choice
        if chart_type == "Bar Chart (Histogram)":
            fig = px.histogram(
                df_resp, 
                x="Option", 
                color="Option",
                title="Aggregate Poll Count",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig.update_layout(showlegend=False, xaxis_title="Selected Answer", yaxis_title="Votes")
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Pie Chart":
            pie_data = df_resp["Option"].value_counts().reset_index()
            pie_data.columns = ["Option", "Count"]
            fig = px.pie(
                pie_data, 
                values="Count", 
                names="Option",
                title="Overall Choice Distribution",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Group Stacked Bar Chart":
            fig = px.histogram(
                df_resp, 
                x="Group", 
                color="Option",
                barmode="group",
                title="Group-wise Poll Breakdown",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(xaxis_title="Groups", yaxis_title="Number of Votes")
            st.plotly_chart(fig, use_container_width=True)

        # Clear poll data button
        if st.button("Reset Poll Data"):
            st.session_state.responses = []
            st.rerun()
