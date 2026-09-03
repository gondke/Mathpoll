import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import string

# ==========================================
# 1. PAGE CONFIGURATION & ANIMATED CSS
# ==========================================
st.set_page_config(
    page_title="STEM Real-Time Polling System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* High contrast metric card */
    .metric-card {
        background-color: #1F2937;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Question Card Styling */
    [data-testid="stVerticalBlock"] > div:has(div.question-marker) {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }

    /* Glowing Blinking Trophy Announcement */
    @keyframes blinkGlow {
        0% { border-color: #FFD700; box-shadow: 0 0 15px #FFD700; }
        50% { border-color: #10B981; box-shadow: 0 0 30px #10B981; }
        100% { border-color: #FFD700; box-shadow: 0 0 15px #FFD700; }
    }
    .winner-box {
        animation: blinkGlow 1.5s infinite alternate;
        background: linear-gradient(135deg, #064E3B 0%, #022C22 100%);
        border: 4px solid #FFD700;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .winner-title {
        color: #FFD700;
        font-size: 2.5em;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    /* Standard Button Polish */
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

# Question Bank State
if "question_bank" not in st.session_state:
    st.session_state.question_bank = [
        {
            "question": r"Eigenvalues of $A = \begin{bmatrix} 2 & 2 \\ 0 & 3 \end{bmatrix}$ are:",
            "option_labels": ["Option A", "Option B", "Option C", "Option D"],
            "options": [
                r"$\lambda_1 = 2, \lambda_2 = 3$",
                r"$\lambda_1 = 0, \lambda_2 = 2$",
                r"$\lambda_1 = 1, \lambda_2 = 3$",
                r"$\lambda_1 = -2, \lambda_2 = -3$"
            ],
            "correct_idx": 0
        },
        {
            "question": r"What is the integral $\int x \, dx$?",
            "option_labels": ["Option A", "Option B", "Option C", "Option D"],
            "options": [r"$\frac{x^2}{2} + C$", r"$x + C$", r"$x^2 + C$", r"$\ln(x) + C$"],
            "correct_idx": 0
        }
    ]

if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "quiz_ended" not in st.session_state:
    st.session_state.quiz_ended = False
if "group_scores" not in st.session_state:
    st.session_state.group_scores = {}

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.title("⚛️ Quiz Master Controls")

st.sidebar.markdown(f"""
<div class="metric-card">
    <span style="color: #9CA3AF; font-size: 0.9em;">Session Code</span><br>
    <span style="color: #60A5FA; font-weight: bold; font-size: 2em; letter-spacing: 3px;">{st.session_state.quiz_code}</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("1. Roster & Grouping")

upload_option = st.sidebar.radio("Input Roster", ["Generate Sample Data (100 Students)", "Upload CSV File"])

if upload_option == "Generate Sample Data (100 Students)":
    if st.sidebar.button("Generate Roster"):
        data = {
            "Roll_No": [f"2026_STEM_{i:03d}" for i in range(1, 101)],
            "Name": [f"Student_{i}" for i in range(1, 101)]
        }
        st.session_state.students_df = pd.DataFrame(data)
        st.sidebar.success("Generated 100 student records!")
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Roll_No, Name)", type=["csv"])
    if uploaded_file:
        st.session_state.students_df = pd.read_csv(uploaded_file)
        st.sidebar.success("Roster Uploaded Successfully!")

if st.session_state.students_df is not None:
    num_groups = st.sidebar.number_input("Number of Groups", min_value=2, max_value=10, value=4)
    if st.sidebar.button("Form Groups"):
        df = st.session_state.students_df.copy().sample(frac=1).reset_index(drop=True)
        st.session_state.groups = {}
        st.session_state.group_scores = {}
        for i in range(num_groups):
            group_name = f"Group {chr(65 + i)}"
            st.session_state.groups[group_name] = df.iloc[i::num_groups]["Roll_No"].tolist()
            st.session_state.group_scores[group_name] = 0
        st.sidebar.success(f"Divided class into {num_groups} groups!")

st.sidebar.markdown("---")
st.sidebar.subheader("2. Analytics Chart View")
chart_type = st.sidebar.selectbox(
    "Visualization Type", 
    ["Individual Group Histograms", "Overall Bar Chart", "Overall Pie Chart", "Group Stacked Bar Chart"]
)

# ==========================================
# 4. TABS: QUESTION BANK / LIVE POLL / ANALYTICS
# ==========================================
st.title("🧪 STEM Real-Time Quiz & Analytics System")

tab_portal, tab_analytics = st.tabs([
    "📲 Student Portal & Question Bank", 
    "📺 Live Classroom Analytics & Leaderboard"
])

curr_q = st.session_state.question_bank[st.session_state.current_q_idx]

# ------------------------------------------
# TAB 1: QUESTION BANK & STUDENT PORTAL
# ------------------------------------------
with tab_portal:
    # Multiple Question Manager
    with st.expander("📚 Question Bank Manager (Add / Select Questions)", expanded=False):
        st.markdown("### Manage Quiz Questions")
        
        # Display available questions selector
        q_options = [f"Q{i+1}: {q['question'][:40]}..." for i, q in enumerate(st.session_state.question_bank)]
        selected_q = st.selectbox("Active Question On Board:", range(len(q_options)), index=st.session_state.current_q_idx)
        
        if selected_q != st.session_state.current_q_idx:
            st.session_state.current_q_idx = selected_q
            st.rerun()

        st.markdown("---")
        st.markdown("**Add New MCQ to Bank:**")
        new_q_text = st.text_input("New Question Text (LaTeX supported):", value=r"What is $\sqrt{16}$?")
        new_op0 = st.text_input("Option 1:", value="2")
        new_op1 = st.text_input("Option 2:", value="4")
        new_op2 = st.text_input("Option 3:", value="8")
        new_op3 = st.text_input("Option 4:", value="16")
        correct_target = st.selectbox("Correct Answer Option:", [0, 1, 2, 3], format_func=lambda x: f"Option {x+1}")

        if st.button("Add Question to Bank ➕"):
            st.session_state.question_bank.append({
                "question": new_q_text,
                "option_labels": ["Option A", "Option B", "Option C", "Option D"],
                "options": [new_op0, new_op1, new_op2, new_op3],
                "correct_idx": correct_target
            })
            st.success("Added new question to quiz bank!")
            st.rerun()

    # Active Question Display
    with st.container():
        st.markdown('<div class="question-marker"></div>', unsafe_allow_html=True)
        st.markdown(f"### Question {st.session_state.current_q_idx + 1} of {len(st.session_state.question_bank)}")
        st.markdown(f"**{curr_q['question']}**")

    # Quiz Navigation Controls for Teacher
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        if st.button("⬅️ Previous Question") and st.session_state.current_q_idx > 0:
            st.session_state.current_q_idx -= 1
            st.rerun()
    with col_nav2:
        if st.button("Next Question ➡️") and st.session_state.current_q_idx < len(st.session_state.question_bank) - 1:
            st.session_state.current_q_idx += 1
            st.rerun()
    with col_nav3:
        if st.button("🏆 End Quiz & Declare Winner"):
            st.session_state.quiz_ended = True
            st.rerun()

    st.markdown("---")
    
    # Student Response Section
    col_stu_input, col_sim = st.columns([1.2, 1])
    
    with col_stu_input:
        st.subheader("📲 Submit Student Answer")
        student_roll = st.text_input("Roll Number:", value="2026_STEM_001")
        
        assigned_group = "Unassigned"
        for grp, members in st.session_state.groups.items():
            if student_roll in members:
                assigned_group = grp
                break
                
        st.info(f"**Group:** {assigned_group}")
        
        formatted_choices = [
            f"**{curr_q['option_labels'][i]}:** {curr_q['options'][i]}" 
            for i in range(len(curr_q['options']))
        ]
        
        selected_idx = st.radio(
            label="Choices",
            options=range(len(formatted_choices)),
            format_func=lambda x: formatted_choices[x],
            label_visibility="collapsed"
        )
        
        if st.button("Submit Answer 🚀"):
            if assigned_group == "Unassigned":
                st.error("Form groups in the sidebar first!")
            else:
                st.session_state.responses.append({
                    "Q_Idx": st.session_state.current_q_idx,
                    "Roll_No": student_roll,
                    "Group": assigned_group,
                    "Option_Index": selected_idx,
                    "Label": curr_q['option_labels'][selected_idx]
                })
                st.success("Response recorded!")

    with col_sim:
        st.subheader("⚡ Simulation Tool")
        st.write("Simulate student responses across all groups:")
        if st.button("Simulate Random Class Responses"):
            if not st.session_state.groups:
                st.warning("Form groups first in sidebar!")
            else:
                for grp, members in st.session_state.groups.items():
                    for student in members:
                        rand_idx = random.randint(0, len(curr_q['options']) - 1)
                        st.session_state.responses.append({
                            "Q_Idx": st.session_state.current_q_idx,
                            "Roll_No": student,
                            "Group": grp,
                            "Option_Index": rand_idx,
                            "Label": curr_q['option_labels'][rand_idx]
                        })
                st.rerun()

# ------------------------------------------
# TAB 2: LIVE ANALYTICS & WINNER DECLARATION
# ------------------------------------------
with tab_analytics:
    # 1. QUIZ ENDED WINNER ANNOUNCEMENT
    if st.session_state.quiz_ended:
        st.balloons()
        
        # Calculate group leaderboard across all questions
        scores = {grp: 0 for grp in st.session_state.groups.keys()}
        df_all = pd.DataFrame(st.session_state.responses)
        
        if not df_all.empty and "Option_Index" in df_all.columns:
            for q_i, q_data in enumerate(st.session_state.question_bank):
                correct_idx = q_data["correct_idx"]
                q_responses = df_all[df_all["Q_Idx"] == q_i]
                
                # Check correct votes count per group
                for grp in scores.keys():
                    grp_correct_votes = len(q_responses[(q_responses["Group"] == grp) & (q_responses["Option_Index"] == correct_idx)])
                    scores[grp] += grp_correct_votes * 10  # 10 points per correct student answer
                    
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_group = sorted_scores[0][0] if sorted_scores else "N/A"
        winning_score = sorted_scores[0][1] if sorted_scores else 0

        st.markdown(f"""
        <div class="winner-box">
            <div class="winner-title">🎉 CONGRATULATIONS {winner_group.upper()}! 🎉</div>
            <p style="font-size: 1.5em; color: #E5E7EB; margin-top: 10px;">
                WINNER OF THE STEM QUIZ SESSION WITH <strong>{winning_score} POINTS</strong>!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Restart Quiz Session 🔄"):
            st.session_state.quiz_ended = False
            st.session_state.responses = []
            st.rerun()

    # 2. LIVE POLL ANALYTICS
    st.markdown(f"## 📊 Live Poll Analysis — Question {st.session_state.current_q_idx + 1}")
    
    df_resp = pd.DataFrame(st.session_state.responses)
    df_curr = df_resp[df_resp["Q_Idx"] == st.session_state.current_q_idx] if not df_resp.empty and "Q_Idx" in df_resp.columns else pd.DataFrame()
    
    if df_curr.empty or "Option_Index" not in df_curr.columns:
        st.warning("No responses yet for this active question. Submit votes in the Student Portal tab!")
    else:
        total_votes = len(df_curr)
        correct_idx = curr_q["correct_idx"]
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.metric(label="Total Votes", value=total_votes)
            st.info(f"**Correct Key:** {curr_q['option_labels'][correct_idx]}")
        with col_m2:
            st.markdown(f"**Question:** {curr_q['question']}")

        st.markdown("---")

        def get_highlight_colors(values, default_color="#3B82F6", max_color="#10B981"):
            if not values or max(values) == 0:
                return [default_color] * len(values)
            max_val = max(values)
            return [max_color if v == max_val else default_color for v in values]

        # 1. GROUP HISTOGRAMS
        if chart_type == "Individual Group Histograms":
            unique_groups = sorted(list(st.session_state.groups.keys()))
            num_g = len(unique_groups)
            
            if num_g > 0:
                cols = 2
                rows = (num_g + 1) // 2
                
                fig = make_subplots(
                    rows=rows, cols=cols, 
                    subplot_titles=[f"Group: {g}" for g in unique_groups],
                    vertical_spacing=0.2, horizontal_spacing=0.12
                )
                
                x_labels = curr_q["option_labels"]
                
                for idx, grp in enumerate(unique_groups):
                    row = (idx // cols) + 1
                    col = (idx % cols) + 1
                    
                    grp_data = df_curr[df_curr["Group"] == grp]
                    grp_total = len(grp_data)
                    
                    counts = grp_data["Option_Index"].value_counts()
                    y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
                    
                    pct_texts = [
                        f"{y_counts[i]} ({y_counts[i]/grp_total*100:.1f}%)" if grp_total > 0 else "0 (0%)" 
                        for i in range(len(x_labels))
                    ]
                    
                    bar_colors = get_highlight_colors(y_counts, default_color="#6366F1", max_color="#10B981")
                    
                    fig.add_trace(
                        go.Bar(
                            x=x_labels, y=y_counts, text=pct_texts, textposition="auto",
                            marker_color=bar_colors, marker_line_color="#FFFFFF", marker_line_width=1.5,
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                
                fig.update_layout(template="plotly_dark", height=300 * rows, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

        # 2. OVERALL BAR CHART
        elif chart_type == "Overall Bar Chart":
            counts = df_curr["Option_Index"].value_counts()
            x_labels = curr_q["option_labels"]
            y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
            
            pct_texts = [f"{v} ({v/total_votes*100:.1f}%)" for v in y_counts]
            bar_colors = get_highlight_colors(y_counts, default_color="#3B82F6", max_color="#10B981")
            
            fig = go.Figure(data=[
                go.Bar(
                    x=x_labels, y=y_counts, text=pct_texts, textposition="auto",
                    marker_color=bar_colors, marker_line_color="#FFFFFF", marker_line_width=2
                )
            ])
            fig.update_layout(
                title="Overall Response Distribution (Highest Bar Highlighted Green)",
                template="plotly_dark", xaxis_title="Options", yaxis_title="Vote Count", height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # 3. OVERALL PIE CHART
        elif chart_type == "Overall Pie Chart":
            pie_data = df_curr["Label"].value_counts().reset_index()
            pie_data.columns = ["Label", "Count"]
            
            fig = px.pie(
                pie_data, values="Count", names="Label",
                title="Percentage Distribution Across Options",
                template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

        # 4. GROUP STACKED BAR CHART
        elif chart_type == "Group Stacked Bar Chart":
            fig = px.histogram(
                df_curr, x="Group", color="Label", barmode="group",
                title="Group-wise Response Comparison",
                template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold, text_auto=True
            )
            fig.update_layout(xaxis_title="Groups", yaxis_title="Votes", height=500)
            st.plotly_chart(fig, use_container_width=True)
