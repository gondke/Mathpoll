import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import string
import sqlite3
import json

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="STEM Quiz & Database Management System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .metric-card {
        background-color: #1F2937;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    [data-testid="stVerticalBlock"] > div:has(div.question-marker) {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
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
        margin: 20px 0;
    }
    .winner-title { color: #FFD700; font-size: 2.5em; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SQLITE DATABASE ENGINE & HELPER FUNCTIONS
# ==========================================
DB_FILE = "quiz_system.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Classrooms Table
    c.execute('''CREATE TABLE IF NOT EXISTS classrooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT UNIQUE NOT NULL
                )''')
    # Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    roll_no TEXT NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY(class_id) REFERENCES classrooms(id)
                )''')
    # Permanent Groups Table
    c.execute('''CREATE TABLE IF NOT EXISTS student_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    group_name TEXT NOT NULL,
                    roll_no TEXT NOT NULL,
                    FOREIGN KEY(class_id) REFERENCES classrooms(id)
                )''')
    # Topic-wise Question Bank Table
    c.execute('''CREATE TABLE IF NOT EXISTS question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    question TEXT NOT NULL,
                    option_labels TEXT NOT NULL,
                    options TEXT NOT NULL,
                    correct_idx INTEGER NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "quiz_code" not in st.session_state:
    st.session_state.quiz_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
if "active_class_id" not in st.session_state:
    st.session_state.active_class_id = None
if "groups" not in st.session_state:
    st.session_state.groups = {}
if "responses" not in st.session_state:
    st.session_state.responses = []
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "quiz_ended" not in st.session_state:
    st.session_state.quiz_ended = False

# ==========================================
# 4. SIDEBAR CONTROLS & SESSION CODE
# ==========================================
st.sidebar.title("⚛️ Teacher Dashboard")

st.sidebar.markdown(f"""
<div class="metric-card">
    <span style="color: #9CA3AF; font-size: 0.9em;">Session Code</span><br>
    <span style="color: #60A5FA; font-weight: bold; font-size: 2em; letter-spacing: 3px;">{st.session_state.quiz_code}</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Visualization Type")
chart_type = st.sidebar.selectbox(
    "Select Chart", 
    ["Individual Group Histograms", "Overall Bar Chart", "Overall Pie Chart", "Group Stacked Bar Chart"]
)

# ==========================================
# 5. MAIN NAVIGATION TABS
# ==========================================
st.title("🧪 STEM Live Quiz & Classroom Manager")

tab_class_db, tab_q_db, tab_portal, tab_analytics = st.tabs([
    "🏫 Classroom & Group DB Manager", 
    "📚 Topic-Wise Question Bank DB", 
    "📲 Student Portal & Live Quiz", 
    "📺 Live Analytics & Leaderboard"
])

# ------------------------------------------
# TAB 1: CLASSROOM & GROUP DATABASE MANAGER
# ------------------------------------------
with tab_class_db:
    st.header("🗄️ Permanent Classroom & Group Roster Database")
    col_c1, col_c2 = st.columns([1, 1])

    conn = get_db_connection()
    
    with col_c1:
        st.subheader("1. Create / Manage Classrooms")
        new_class = st.text_input("New Classroom Name (e.g., 'Grade 10 Physics'):")
        if st.button("Create Classroom ➕"):
            if new_class:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO classrooms (class_name) VALUES (?)", (new_class,))
                    conn.commit()
                    st.success(f"Classroom '{new_class}' created!")
                except sqlite3.IntegrityError:
                    st.error("Classroom name already exists!")

        # Load Existing Classrooms
        classes_df = pd.read_sql("SELECT * FROM classrooms", conn)
        if not classes_df.empty:
            selected_class_name = st.selectbox("Select Active Classroom:", classes_df["class_name"].tolist())
            selected_class_row = classes_df[classes_df["class_name"] == selected_class_name].iloc[0]
            st.session_state.active_class_id = int(selected_class_row["id"])
            
            st.markdown("---")
            st.subheader(f"2. Add Students to '{selected_class_name}'")
            
            upload_type = st.radio("Student Input Method", ["CSV Upload", "Manual Entry"])
            if upload_type == "CSV Upload":
                up_file = st.file_uploader("Upload CSV (Columns: Roll_No, Name)", type=["csv"])
                if up_file and st.button("Save Students to Database"):
                    df_up = pd.read_csv(up_file)
                    for _, row in df_up.iterrows():
                        conn.execute("INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)", 
                                     (st.session_state.active_class_id, str(row["Roll_No"]), str(row["Name"])))
                    conn.commit()
                    st.success("Uploaded and saved students into classroom DB!")
            else:
                s_roll = st.text_input("Roll Number:")
                s_name = st.text_input("Student Name:")
                if st.button("Add Student"):
                    conn.execute("INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)", 
                                 (st.session_state.active_class_id, s_roll, s_name))
                    conn.commit()
                    st.success(f"Added {s_name}!")

    with col_c2:
        st.subheader("3. Classroom Roster & Group Formation")
        if st.session_state.active_class_id:
            students_in_class = pd.read_sql(
                "SELECT roll_no, name FROM students WHERE class_id = ?", 
                conn, params=(st.session_state.active_class_id,)
            )
            st.write(f"Total Enrolled Students: **{len(students_in_class)}**")
            st.dataframe(students_in_class, height=180, use_container_width=True)

            st.markdown("---")
            st.subheader("Group Formation Controls")
            num_g = st.number_input("Number of Groups to Form", min_value=2, max_value=10, value=4)
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if st.button("Auto-Form & Save Groups 🎲"):
                    if not students_in_class.empty:
                        conn.execute("DELETE FROM student_groups WHERE class_id = ?", (st.session_state.active_class_id,))
                        shuffled_rolls = students_in_class["roll_no"].sample(frac=1).tolist()
                        st.session_state.groups = {}
                        for i in range(num_g):
                            grp_name = f"Group {chr(65 + i)}"
                            members = shuffled_rolls[i::num_g]
                            st.session_state.groups[grp_name] = members
                            for r_no in members:
                                conn.execute("INSERT INTO student_groups (class_id, group_name, roll_no) VALUES (?, ?, ?)",
                                             (st.session_state.active_class_id, grp_name, r_no))
                        conn.commit()
                        st.success(f"Formed {num_g} groups and stored in Database!")
            
            with col_g2:
                if st.button("Dissolve Groups ❌"):
                    conn.execute("DELETE FROM student_groups WHERE class_id = ?", (st.session_state.active_class_id,))
                    conn.commit()
                    st.session_state.groups = {}
                    st.warning("Groups dissolved for this classroom.")

            # Load Saved Groups from DB
            saved_grps = pd.read_sql(
                "SELECT group_name, roll_no FROM student_groups WHERE class_id = ?", 
                conn, params=(st.session_state.active_class_id,)
            )
            if not saved_grps.empty:
                st.session_state.groups = saved_grps.groupby("group_name")["roll_no"].apply(list).to_dict()
                st.write("**Current Active Groups in Class:**")
                st.json(st.session_state.groups)

    conn.close()

# ------------------------------------------
# TAB 2: TOPIC-WISE QUESTION BANK DATABASE
# ------------------------------------------
with tab_q_db:
    st.header("📚 Topic-Wise Question Bank Database")
    conn = get_db_connection()

    col_q1, col_q2 = st.columns([1, 1])

    with col_q1:
        st.subheader("1. Add Question to Database")
        q_topic = st.text_input("Topic Name (e.g., 'Linear Algebra', 'Calculus'):", value="Linear Algebra")
        q_text = st.text_area("Question Text (LaTeX Supported):", value=r"Eigenvalues of $A = \begin{bmatrix} 2 & 2 \\ 0 & 3 \end{bmatrix}$ are:")
        
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            op_a = st.text_input("Option A:", value=r"$\lambda_1 = 2, \lambda_2 = 3$")
            op_b = st.text_input("Option B:", value=r"$\lambda_1 = 0, \lambda_2 = 2$")
        with col_op2:
            op_c = st.text_input("Option C:", value=r"$\lambda_1 = 1, \lambda_2 = 3$")
            op_d = st.text_input("Option D:", value=r"$\lambda_1 = -2, \lambda_2 = -3$")

        correct_op = st.selectbox("Correct Option Index:", [0, 1, 2, 3], format_func=lambda x: f"Option {chr(65+x)}")

        if st.button("Save Question to DB 💾"):
            conn.execute(
                "INSERT INTO question_bank (topic, question, option_labels, options, correct_idx) VALUES (?, ?, ?, ?, ?)",
                (q_topic, q_text, json.dumps(["Option A", "Option B", "Option C", "Option D"]), json.dumps([op_a, op_b, op_c, op_d]), correct_op)
            )
            conn.commit()
            st.success("Question saved to database topic-wise!")

    with col_q2:
        st.subheader("2. Import Topic Questions to Live Quiz")
        q_bank_df = pd.read_sql("SELECT * FROM question_bank", conn)
        
        if not q_bank_df.empty:
            topics = q_bank_df["topic"].unique().tolist()
            selected_topic = st.selectbox("Filter Question Bank by Topic:", topics)
            
            filtered_qs = q_bank_df[q_bank_df["topic"] == selected_topic]
            st.dataframe(filtered_qs[["id", "topic", "question"]], use_container_width=True)
            
            if st.button("Import All Questions in Topic to Active Quiz 🚀"):
                st.session_state.quiz_questions = []
                for _, row in filtered_qs.iterrows():
                    st.session_state.quiz_questions.append({
                        "question": row["question"],
                        "option_labels": json.loads(row["option_labels"]),
                        "options": json.loads(row["options"]),
                        "correct_idx": int(row["correct_idx"])
                    })
                st.session_state.current_q_idx = 0
                st.success(f"Imported {len(filtered_qs)} questions into active quiz session!")
        else:
            st.info("No questions stored in database yet.")

    conn.close()

# ------------------------------------------
# TAB 3: STUDENT PORTAL & LIVE QUIZ
# ------------------------------------------
with tab_portal:
    if not st.session_state.quiz_questions:
        st.warning("No active quiz questions! Go to 'Topic-Wise Question Bank DB' tab and import questions to start.")
    else:
        curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]

        with st.container():
            st.markdown('<div class="question-marker"></div>', unsafe_allow_html=True)
            st.markdown(f"### Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}")
            st.markdown(f"**{curr_q['question']}**")

        # Navigation Controls
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            if st.button("⬅️ Previous Question") and st.session_state.current_q_idx > 0:
                st.session_state.current_q_idx -= 1
                st.rerun()
        with col_nav2:
            if st.button("Next Question ➡️") and st.session_state.current_q_idx < len(st.session_state.quiz_questions) - 1:
                st.session_state.current_q_idx += 1
                st.rerun()
        with col_nav3:
            if st.button("🏆 End Quiz & Declare Winner"):
                st.session_state.quiz_ended = True
                st.rerun()

        st.markdown("---")
        
        # Student Voting Interface
        col_stu_input, col_sim = st.columns([1.2, 1])
        
        with col_stu_input:
            st.subheader("📲 Submit Student Response")
            student_roll = st.text_input("Roll Number:", value="2026_STEM_001")
            
            assigned_group = "Unassigned"
            for grp, members in st.session_state.groups.items():
                if student_roll in members:
                    assigned_group = grp
                    break
                    
            st.info(f"**Assigned Group:** {assigned_group}")
            
            choices = [f"**{curr_q['option_labels'][i]}:** {curr_q['options'][i]}" for i in range(len(curr_q['options']))]
            
            selected_idx = st.radio(
                label="Options", options=range(len(choices)), 
                format_func=lambda x: choices[x], label_visibility="collapsed"
            )
            
            if st.button("Submit Vote 🚀"):
                if assigned_group == "Unassigned":
                    st.error("Form/load classroom groups first!")
                else:
                    st.session_state.responses.append({
                        "Q_Idx": st.session_state.current_q_idx,
                        "Roll_No": student_roll,
                        "Group": assigned_group,
                        "Option_Index": selected_idx,
                        "Label": curr_q['option_labels'][selected_idx]
                    })
                    st.success("Response recorded in database session!")

        with col_sim:
            st.subheader("⚡ Simulation Tool")
            if st.button("Simulate Random Class Responses"):
                if not st.session_state.groups:
                    st.warning("Form/load classroom groups first!")
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
# TAB 4: LIVE ANALYTICS & LEADERBOARD
# ------------------------------------------
with tab_analytics:
    # WINNER DECLARATION
    if st.session_state.quiz_ended:
        st.balloons()
        
        scores = {grp: 0 for grp in st.session_state.groups.keys()}
        df_all = pd.DataFrame(st.session_state.responses)
        
        if not df_all.empty and "Option_Index" in df_all.columns:
            for q_i, q_data in enumerate(st.session_state.quiz_questions):
                correct_idx = q_data["correct_idx"]
                q_responses = df_all[df_all["Q_Idx"] == q_i]
                for grp in scores.keys():
                    correct_votes = len(q_responses[(q_responses["Group"] == grp) & (q_responses["Option_Index"] == correct_idx)])
                    scores[grp] += correct_votes * 10
                    
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner_group = sorted_scores[0][0] if sorted_scores else "N/A"
        winning_score = sorted_scores[0][1] if sorted_scores else 0

        st.markdown(f"""
        <div class="winner-box">
            <div class="winner-title">🎉 CONGRATULATIONS {winner_group.upper()}! 🎉</div>
            <p style="font-size: 1.5em; color: #E5E7EB;">
                VICTORIOUS GROUP WITH <strong>{winning_score} TOTAL POINTS</strong>!
            </p>
        </div>
        """, unsafe_allow_html=True)

    # LIVE POLL ANALYTICS
    st.markdown(f"## 📊 Live Poll Analytics")
    
    if not st.session_state.quiz_questions:
        st.warning("No active quiz running.")
    else:
        df_resp = pd.DataFrame(st.session_state.responses)
        df_curr = df_resp[df_resp["Q_Idx"] == st.session_state.current_q_idx] if not df_resp.empty and "Q_Idx" in df_resp.columns else pd.DataFrame()
        
        if df_curr.empty:
            st.warning("Awaiting responses for the current question...")
        else:
            curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]
            total_votes = len(df_curr)
            
            col_m1, col_m2 = st.columns([1, 4])
            with col_m1:
                st.metric("Total Votes", total_votes)
            with col_m2:
                st.markdown(f"**Question:** {curr_q['question']}")

            st.markdown("---")

            def get_highlight_colors(values, default_color="#3B82F6", max_color="#10B981"):
                if not values or max(values) == 0:
                    return [default_color] * len(values)
                return [max_color if v == max(values) else default_color for v in values]

            if chart_type == "Individual Group Histograms":
                unique_groups = sorted(list(st.session_state.groups.keys()))
                if unique_groups:
                    cols = 2
                    rows = (len(unique_groups) + 1) // 2
                    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[f"Group: {g}" for g in unique_groups], vertical_spacing=0.2)
                    x_labels = curr_q["option_labels"]
                    
                    for idx, grp in enumerate(unique_groups):
                        r, c = (idx // cols) + 1, (idx % cols) + 1
                        grp_data = df_curr[df_curr["Group"] == grp]
                        counts = grp_data["Option_Index"].value_counts()
                        y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
                        pct_texts = [f"{v} ({v/len(grp_data)*100:.1f}%)" if len(grp_data) > 0 else "0 (0%)" for v in y_counts]
                        
                        fig.add_trace(go.Bar(x=x_labels, y=y_counts, text=pct_texts, textposition="auto",
                                             marker_color=get_highlight_colors(y_counts), showlegend=False), row=r, col=c)
                    
                    fig.update_layout(template="plotly_dark", height=300 * rows)
                    st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Overall Bar Chart":
                counts = df_curr["Option_Index"].value_counts()
                x_labels = curr_q["option_labels"]
                y_counts = [counts.get(i, 0) for i in range(len(x_labels))]
                pct_texts = [f"{v} ({v/total_votes*100:.1f}%)" for v in y_counts]
                
                fig = go.Figure(data=[go.Bar(x=x_labels, y=y_counts, text=pct_texts, textposition="auto", marker_color=get_highlight_colors(y_counts))])
                fig.update_layout(title="Class Total Responses", template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Overall Pie Chart":
                pie_data = df_curr["Label"].value_counts().reset_index()
                pie_data.columns = ["Label", "Count"]
                fig = px.pie(pie_data, values="Count", names="Label", template="plotly_dark")
                fig.update_traces(textposition='inside', textinfo='percent+label+value')
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Group Stacked Bar Chart":
                fig = px.histogram(df_curr, x="Group", color="Label", barmode="group", template="plotly_dark", text_auto=True)
                st.plotly_chart(fig, use_container_width=True)
