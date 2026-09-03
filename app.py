import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import string

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="MathPhys Chem Real-Time Polling",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast CSS
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* High contrast card metric */
    .metric-card {
        background-color: #1F2937;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Target Streamlit's container element to style it as the Question Box */
    [data-testid="stVerticalBlock"] > div:has(div.question-marker) {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 20px;
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

# Default question
if "question" not in st.session_state:
    st.session_state.question = r"Eigenvalues of the matrix $$A = \begin{bmatrix} 2 & 2 \\ 0 & 3 \end{bmatrix}$$ are:"
if "options" not in st.session_state:
    st.session_state.options = [
        r"$\lambda_1 = 2, \lambda_2 = 3$",
        r"$\lambda_1 = 0, \lambda_2 = 2$",
        r"$\lambda_1 = 1, \lambda_2 = 3$",
        r"$\lambda_1 = -2, \lambda_2 = -3$"
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
            df = df.sample(frac=1).reset_index(drop=True)
            st.session_state.groups = {}
            for i in range(num_groups):
                group_name = f"Group {chr(65 + i)}"
                st.session_state.groups[group_name] = df.iloc[i::num_groups]["Roll_No"].tolist()
            st.sidebar.success(f"Divided {len(df)} students into {num_groups} groups!")

st.sidebar.markdown("---")
st.sidebar.subheader("2. Chart Configuration")
chart_type = st.sidebar.selectbox(
    "Visualization Type", 
    ["Individual Group Histograms", "Overall Bar Chart", "Overall Pie Chart", "Group Stacked Bar Chart"]
)

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🧪 STEM Live Real-Time Polling System")

# TeX Question Editor
with st.expander("📝 Question & LaTeX Editor", expanded=False):
    st.session_state.question = st.text_input("Enter Question (Use $...$ for inline or $$\\dots$$ for block LaTeX):", value=st.session_state.question)
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.options[0] = st.text_input("Option A", value=st.session_state.options[0])
        st.session_state.options[1] = st.text_input("Option B", value=st.session_state.options[1])
    with col_b:
        st.session_state.options[2] = st.text_input("Option C", value=st.session_state.options[2])
        st.session_state.options[3] = st.text_input("Option D", value=st.session_state.options[3])

# Question Box
with st.container():
    st.markdown('<div class="question-marker"></div>', unsafe_allow_html=True)
    st.markdown("### Current Question:")
    st.markdown(st.session_state.question)

# Main Grid Layout: Student Portal (Left) | Live Analytics (Right)
col_student, col_analytics = st.columns([1, 1.3])

# ------------------------------------------
# STUDENT SIMULATOR / INTERFACE (Left Column)
# ------------------------------------------
with col_student:
    st.subheader("📲 Student Response Portal")
    
    student_roll = st.text_input("Enter Your Roll Number:", value="2026_STEM_001")
    
    assigned_group = "Unassigned"
    for grp, members in st.session_state.groups.items():
        if student_roll in members:
            assigned_group = grp
            break
            
    st.info(f"**Assigned Group:** {assigned_group}")
    
    st.write("**Select the correct option:**")
    selected_option = st.radio(
        label="Options",
        options=st.session_state.options,
        label_visibility="collapsed"
    )
    
    if st.button("Submit Answer 🚀"):
        if assigned_group == "Unassigned":
            st.error("Please form groups in the sidebar first!")
        else:
            st.session_state.responses.append({
                "Roll_No": student_roll,
                "Group": assigned_group,
                "Option": selected_option
            })
            st.success("Response recorded in real-time!")

    st.markdown("---")
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
        st.metric(label="Total Live Responses Received", value=len(df_resp))
        
        # 1. INDIVIDUAL GROUP HISTOGRAMS
        if chart_type == "Individual Group Histograms":
            unique_groups = sorted(list(st.session_state.groups.keys()))
            num_g = len(unique_groups)
            
            if num_g == 0:
                st.warning("No groups formed yet!")
            else:
                # Determine subplot layout grid (e.g. 2 columns)
                cols = 2
                rows = (num_g + 1) // 2
                
                fig = make_subplots(
                    rows=rows, 
                    cols=cols, 
                    subplot_titles=[f"Histogram - {g}" for g in unique_groups],
                    vertical_spacing=0.15,
                    horizontal_spacing=0.1
                )
                
                # Colors mapped to the options
                color_map = {
                    st.session_state.options[0]: "#3B82F6",
                    st.session_state.options[1]: "#10B981",
                    st.session_state.options[2]: "#F59E0B",
                    st.session_state.options[3]: "#EF4444"
                }
                
                for idx, grp in enumerate(unique_groups):
                    row = (idx // cols) + 1
                    col = (idx % cols) + 1
                    
                    grp_data = df_resp[df_resp["Group"] == grp]
                    
                    # Count responses per option for this group
                    counts = grp_data["Option"].value_counts()
                    
                    x_vals = st.session_state.options
                    y_vals = [counts.get(opt, 0) for opt in x_vals]
                    
                    # Create bar plot for each group
                    fig.add_trace(
                        go.Bar(
                            x=[f"Opt {i+1}" for i in range(len(x_vals))],
                            y=y_vals,
                            name=grp,
                            marker_color=["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                
                fig.update_layout(
                    template="plotly_dark",
                    height=250 * rows,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

        # 2. OVERALL BAR CHART
        elif chart_type == "Overall Bar Chart":
            fig = px.histogram(
                df_resp, 
                x="Option", 
                color="Option",
                title="Aggregate Class Poll",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig.update_layout(showlegend=False, xaxis_title="Selected Answer", yaxis_title="Votes")
            st.plotly_chart(fig, use_container_width=True)

        # 3. OVERALL PIE CHART
        elif chart_type == "Overall Pie Chart":
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

        # 4. GROUP STACKED BAR CHART
        elif chart_type == "Group Stacked Bar Chart":
            fig = px.histogram(
                df_resp, 
                x="Group", 
                color="Option",
                barmode="group",
                title="Group-wise Poll Comparison",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(xaxis_title="Groups", yaxis_title="Number of Votes")
            st.plotly_chart(fig, use_container_width=True)

        if st.button("Reset Poll Data"):
            st.session_state.responses = []
            st.rerun()
