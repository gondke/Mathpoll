import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import string

# ==========================================
# 1. PAGE CONFIGURATION & HIGH-CONTRAST STYLING
# ==========================================
st.set_page_config(
    page_title="STEM Real-Time Polling System",
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
    
    /* High contrast cards */
    .metric-card {
        background-color: #1F2937;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Styled Question Box */
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

# Default Linear Algebra / Physics question
if "question" not in st.session_state:
    st.session_state.question = r"Eigenvalues of the matrix $$A = \begin{bmatrix} 2 & 2 \\ 0 & 3 \end{bmatrix}$$ are:"
if "option_labels" not in st.session_state:
    st.session_state.option_labels = ["A", "B", "C", "D"]
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
# 4. NAVIGATION TABS (SEPARATE ANALYTICS PAGE)
# ==========================================
st.title("🧪 STEM Live Real-Time Polling System")

tab_portal, tab_analytics = st.tabs([
    "📲 Student Portal & Question Editor", 
    "📺 Live Classroom Analytics (Full Screen Display)"
])

# ------------------------------------------
# TAB 1: QUESTION EDITOR & STUDENT PORTAL
# ------------------------------------------
with tab_portal:
    # Flexible TeX Question & Options Editor
    with st.expander("📝 Question & Flexible Option Editor", expanded=True):
        st.session_state.question = st.text_input(
            "Enter Question (Use $...$ for inline or $$\\dots$$ for block LaTeX):", 
            value=st.session_state.question
        )
        
        st.markdown("**Option Prefixes / Symbols:**")
        prefix_preset = st.radio(
            "Select Prefix Preset or Choose Custom:",
            ["A, B, C, D", "1, 2, 3, 4", "(i), (ii), (iii), (iv)", "Custom Symbols"],
            horizontal=True
        )
        
        if prefix_preset == "A, B, C, D":
            st.session_state.option_labels = ["Option A", "Option B", "Option C", "Option D"]
        elif prefix_preset == "1, 2, 3, 4":
            st.session_state.option_labels = ["Option 1", "Option 2", "Option 3", "Option 4"]
        elif prefix_preset == "(i), (ii), (iii), (iv)":
            st.session_state.option_labels = ["Option (i)", "Option (ii)", "Option (iii)", "Option (iv)"]
        
        col_lbl1, col_lbl2, col_lbl3, col_lbl4 = st.columns(4)
        if prefix_preset == "Custom Symbols":
            with col_lbl1:
                st.session_state.option_labels[0] = st.text_input("Label 1", value=st.session_state.option_labels[0])
            with col_lbl2:
                st.session_state.option_labels[1] = st.text_input("Label 2", value=st.session_state.option_labels[1])
            with col_lbl3:
                st.session_state.option_labels[2] = st.text_input("Label 3", value=st.session_state.option_labels[2])
            with col_lbl4:
                st.session_state.option_labels[3] = st.text_input("Label 4", value=st.session_state.option_labels[3])

        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.options[0] = st.text_input(f"Content for {st.session_state.option_labels[0]}", value=st.session_state.options[0])
            st.session_state.options[1] = st.text_input(f"Content for {st.session_state.option_labels[1]}", value=st.session_state.options[1])
        with col_b:
            st.session_state.options[2] = st.text_input(f"Content for {st.session_state.option_labels[2]}", value=st.session_state.options[2])
            st.session_state.options[3] = st.text_input(f"Content for {st.session_state.option_labels[3]}", value=st.session_state.options[3])

    # Current Question Card
    with st.container():
        st.markdown('<div class="question-marker"></div>', unsafe_allow_html=True)
        st.markdown("### Current Question:")
        st.markdown(st.session_state.question)

    st.markdown("---")
    
    # Student Interface
    col_stu_input, col_sim = st.columns([1.2, 1])
    
    with col_stu_input:
        st.subheader("📲 Submit Response")
        student_roll = st.text_input("Enter Your Roll Number:", value="2026_STEM_001")
        
        assigned_group = "Unassigned"
        for grp, members in st.session_state.groups.items():
            if student_roll in members:
                assigned_group = grp
                break
                
        st.info(f"**Assigned Group:** {assigned_group}")
        
        # Combine Label + Content for Radio Display
        formatted_choices = [
            f"**{st.session_state.option_labels[i]}:** {st.session_state.options[i]}" 
            for i in range(len(st.session_state.options))
        ]
        
        selected_idx = st.radio(
            label="Options",
            options=range(len(formatted_choices)),
            format_func=lambda x: formatted_choices[x],
            label_visibility="collapsed"
        )
        
        if st.button("Submit Answer 🚀"):
            if assigned_group == "Unassigned":
                st.error("Please form groups in the sidebar first!")
            else:
                st.session_state.responses.append({
                    "Roll_No": student_roll,
                    "Group": assigned_group,
                    "Option_Index": selected_idx,
                    "Label": st.session_state.option_labels[selected_idx]
                })
                st.success("Response recorded in real-time!")

    with col_sim:
        st.subheader("⚡ Teacher Quick Test")
        st.write("Simulate 80 student responses to quickly test chart rendering:")
        if st.button("Simulate Random Class Responses (80 Students)"):
            if not st.session_state.groups:
                st.warning("Please setup groups first in the sidebar!")
            else:
                st.session_state.responses = []
                for grp, members in st.session_state.groups.items():
                    for student in members:
                        rand_idx = random.randint(0, len(st.session_state.options) - 1)
                        st.session_state.responses.append({
                            "Roll_No": student,
                            "Group": grp,
                            "Option_Index": rand_idx,
                            "Label": st.session_state.option_labels[rand_idx]
                        })
                st.rerun()

# ------------------------------------------
# TAB 2: LIVE CLASSROOM ANALYTICS (DEDICATED DISPLAY)
# ------------------------------------------
with tab_analytics:
    st.markdown("## 📊 Live Classroom Poll Results")
    
    if len(st.session_state.responses) == 0:
        st.warning("Awaiting live responses from students... Submit votes in the Student Portal tab!")
    else:
        df_resp = pd.DataFrame(st.session_state.responses)
        total_votes = len(df_resp)
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.metric(label="Total Responses", value=total_votes)
            if st.button("Reset Poll Data 🔄"):
                st.session_state.responses = []
                st.rerun()
                
        with col_m2:
            st.markdown(f"**Question:** {st.session_state.question}")

        st.markdown("---")

        # Helper function to get color array highlighting the maximum bar
        def get_highlight_colors(values, default_color="#3B82F6", max_color="#10B981"):
            if not values or max(values) == 0:
                return [default_color] * len(values)
            max_val = max(values)
            return [max_color if v == max_val else default_color for v in values]

        # 1. INDIVIDUAL GROUP HISTOGRAMS
        if chart_type == "Individual Group Histograms":
            unique_groups = sorted(list(st.session_state.groups.keys()))
            num_g = len(unique_groups)
            
            if num_g == 0:
                st.warning("No groups formed yet! Use the sidebar to set up groups.")
            else:
                cols = 2
                rows = (num_g + 1) // 2
                
                fig = make_subplots(
                    rows=rows, 
                    cols=cols, 
                    subplot_titles=[f"Group: {g}" for g in unique_groups],
                    vertical_spacing=0.2,
                    horizontal_spacing=0.12
                )
                
                x_labels = st.session_state.option_labels
                
                for idx, grp in enumerate(unique_groups):
                    row = (idx // cols) + 1
                    col = (idx % cols) + 1
                    
                    grp_data = df_resp[df_resp["Group"] == grp]
                    grp_total = len(grp_data)
                    
                    counts = grp_data["Option_Index"].value_counts()
                    y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
                    
                    # Calculate percentage text
                    pct_texts = [
                        f"{y_counts[i]} ({y_counts[i]/grp_total*100:.1f}%)" if grp_total > 0 else "0 (0%)" 
                        for i in range(len(x_labels))
                    ]
                    
                    # Highest bar color highlight
                    bar_colors = get_highlight_colors(y_counts, default_color="#6366F1", max_color="#10B981")
                    
                    fig.add_trace(
                        go.Bar(
                            x=x_labels,
                            y=y_counts,
                            text=pct_texts,
                            textposition="auto",
                            marker_color=bar_colors,
                            marker_line_color="#FFFFFF",
                            marker_line_width=1.5,
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                
                fig.update_layout(
                    template="plotly_dark",
                    height=300 * rows,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

        # 2. OVERALL BAR CHART
        elif chart_type == "Overall Bar Chart":
            counts = df_resp["Option_Index"].value_counts()
            x_labels = st.session_state.option_labels
            y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
            
            pct_texts = [f"{v} ({v/total_votes*100:.1f}%)" for v in y_counts]
            bar_colors = get_highlight_colors(y_counts, default_color="#3B82F6", max_color="#10B981")
            
            fig = go.Figure(data=[
                go.Bar(
                    x=x_labels,
                    y=y_counts,
                    text=pct_texts,
                    textposition="auto",
                    marker_color=bar_colors,
                    marker_line_color="#FFFFFF",
                    marker_line_width=2
                )
            ])
            fig.update_layout(
                title="Overall Aggregate Class Poll (Highest Option Highlighted in Green)",
                template="plotly_dark",
                xaxis_title="Options",
                yaxis_title="Vote Count",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # 3. OVERALL PIE CHART
        elif chart_type == "Overall Pie Chart":
            pie_data = df_resp["Label"].value_counts().reset_index()
            pie_data.columns = ["Label", "Count"]
            
            fig = px.pie(
                pie_data, 
                values="Count", 
                names="Label",
                title="Overall Choice Percentage Distribution",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        # 4. GROUP STACKED BAR CHART
        elif chart_type == "Group Stacked Bar Chart":
            fig = px.histogram(
                df_resp, 
                x="Group", 
                color="Label",
                barmode="group",
                title="Group-wise Choice Comparison",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold,
                text_auto=True
            )
            fig.update_layout(xaxis_title="Groups", yaxis_title="Number of Votes", height=500)
            st.plotly_chart(fig, use_container_width=True)
