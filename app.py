import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import string
import sqlite3
import json
import base64
from io import BytesIO

# Try importing PyPDF2 for PDF processing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

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
    /* Unified Question Box Styling with Enriched Font Size */
    .unified-question-box {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 28px;
        margin-bottom: 25px;
        font-size: 1.35em !important;
        line-height: 1.6;
    }
    .unified-question-box h2 {
        font-size: 1.7em !important;
        color: #60A5FA !important;
        margin-bottom: 15px;
    }
    .unified-question-box h3 {
        font-size: 1.4em !important;
        color: #FFFFFF !important;
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
# 2. SQLITE DATABASE ENGINE & MIGRATION
# ==========================================
DB_FILE = "quiz_system.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users Table (Teachers)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    # Default Teacher Account
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("teacher1", "admin123"))
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("teacher2", "admin123"))

    # Classrooms Table
    c.execute('''CREATE TABLE IF NOT EXISTS classrooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER,
                    class_name TEXT NOT NULL,
                    FOREIGN KEY(teacher_id) REFERENCES users(id)
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
    # Topic-wise Question Bank Table (Shared across all teachers)
    c.execute('''CREATE TABLE IF NOT EXISTS question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_by TEXT,
                    topic TEXT NOT NULL,
                    question TEXT NOT NULL,
                    option_labels TEXT NOT NULL,
                    options TEXT NOT NULL,
                    correct_idx INTEGER NOT NULL,
                    image_base64 TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "user_role" not in st.session_state:
    st.session_state.user_role = None  # Options: 'Teacher', 'Student'
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None
if "username" not in st.session_state:
    st.session_state.username = None
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
# 4. LOGIN & ROLE SELECTION SYSTEM
# ==========================================
if st.session_state.user_role is None:
    st.title("🧪 STEM Live Quiz Platform")
    st.markdown("### Welcome! Please select your entry mode to continue:")
    
    col_login_t, col_login_s = st.columns(2)

    with col_login_t:
        st.subheader("👨‍🏫 Teacher Portal")
        with st.form("teacher_login_form"):
            t_user = st.text_input("Username", value="teacher1")
            t_pass = st.text_input("Password", type="password", value="admin123")
            submit_teacher = st.form_submit_button("Teacher Login 🔑")

            if submit_teacher:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (t_user, t_pass))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state.user_role = "Teacher"
                    st.session_state.teacher_id = user[0]
                    st.session_state.username = user[1]
                    st.success(f"Welcome back, {user[1]}!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")

    with col_login_s:
        st.subheader("🎓 Student Portal (Join via Session Code)")
        with st.form("student_code_form"):
            entered_code = st.text_input("Enter 6-Digit Session Code:")
            submit_student = st.form_submit_button("Join Live Quiz 🚀")

            if submit_student:
                if entered_code.strip().upper() == st.session_state.quiz_code:
                    st.session_state.user_role = "Student"
                    st.success("Session Code Verified! Redirecting to Quiz...")
                    st.rerun()
                else:
                    st.error("Invalid Session Code! Please check with your teacher.")
    st.stop()

# ==========================================
# 5. STUDENT-ONLY INTERFACE
# ==========================================
if st.session_state.user_role == "Student":
    st.title("📲 Student Live Poll Portal")
    
    conn = get_db_connection()
    classes_df = pd.read_sql("SELECT * FROM classrooms", conn)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        selected_classroom = st.selectbox("Select Classroom:", classes_df["class_name"].tolist() if not classes_df.empty else [])
    
    selected_class_id = None
    students_list = []
    if selected_classroom and not classes_df.empty:
        selected_class_id = int(classes_df[classes_df["class_name"] == selected_classroom].iloc[0]["id"])
        students_df = pd.read_sql("SELECT roll_no, name FROM students WHERE class_id = ?", conn, params=(selected_class_id,))
        students_list = [f"{row['roll_no']} - {row['name']}" for _, row in students_df.iterrows()]
    
    with col_s2:
        selected_student = st.selectbox("Select Your Roll Number & Name:", students_list)
        student_roll = selected_student.split(" - ")[0] if selected_student else ""

    # Fetch Group Assignment
    assigned_group = "Unassigned"
    if selected_class_id and student_roll:
        grp_df = pd.read_sql("SELECT group_name FROM student_groups WHERE class_id = ? AND roll_no = ?", conn, params=(selected_class_id, student_roll))
        if not grp_df.empty:
            assigned_group = grp_df.iloc[0]["group_name"]

    st.info(f"**Assigned Group:** {assigned_group}")
    conn.close()

    st.markdown("---")

    # Display Active Quiz Question
    if not st.session_state.quiz_questions:
        st.warning("Waiting for teacher to start/import quiz questions...")
    else:
        curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]

        # Enriched Font & Unified Question Box
        st.markdown(f"""
        <div class="unified-question-box">
            <h2>Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}</h2>
            <h3>{curr_q['question']}</h3>
        </div>
        """, unsafe_allow_html=True)

        if curr_q.get("image_base64"):
            st.image(f"data:image/png;base64,{curr_q['image_base64']}", use_container_width=True)

        # Options Inside Unified Block Framework
        choices = [f"**{curr_q['option_labels'][i]}:** {curr_q['options'][i]}" for i in range(len(curr_q['options']))]
        selected_idx = st.radio("Choose Option:", options=range(len(choices)), format_func=lambda x: choices[x])

        if st.button("Submit Vote 🚀", use_container_width=True):
            if assigned_group == "Unassigned":
                st.error("You are not assigned to a group in this classroom yet!")
            else:
                st.session_state.responses.append({
                    "Q_Idx": st.session_state.current_q_idx,
                    "Roll_No": student_roll,
                    "Group": assigned_group,
                    "Option_Index": selected_idx,
                    "Label": curr_q['option_labels'][selected_idx]
                })
                st.success("Response recorded successfully!")

    if st.sidebar.button("Logout Student"):
        st.session_state.user_role = None
        st.rerun()
    st.stop()

# ==========================================
# 6. TEACHER DASHBOARD & CONTROLS
# ==========================================
st.sidebar.title(f"👨‍🏫 {st.session_state.username}'s Dashboard")

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
    ["Individual Group Histograms", "Individual Group Pie Charts", "Overall Bar Chart", "Overall Pie Chart", "Group Stacked Bar Chart"]
)

if st.sidebar.button("Logout Teacher 🚪"):
    st.session_state.user_role = None
    st.session_state.teacher_id = None
    st.session_state.username = None
    st.rerun()

# ==========================================
# 7. TEACHER TABS MANAGEMENT
# ==========================================
st.title("🧪 STEM Live Quiz & Private Class Manager")

tab_class_db, tab_q_db, tab_media_quiz, tab_portal, tab_analytics = st.tabs([
    "🏫 Classroom DB (Private)", 
    "📚 Question Bank (Shared DB)", 
    "📷 Image/PDF Quiz Creator",
    "📲 Live Control", 
    "📺 Analytics & Leaderboard"
])

# ------------------------------------------
# TAB 1: TEACHER PRIVATE CLASSROOM & GROUPS
# ------------------------------------------
with tab_class_db:
    st.header(f"🗄️ Private Classroom Roster — {st.session_state.username}")
    col_c1, col_c2 = st.columns([1, 1])

    conn = get_db_connection()
    
    with col_c1:
        st.subheader("1. Create / Select Private Classroom")
        new_class = st.text_input("New Classroom Name (e.g., 'Physics 10B'):")
        if st.button("Create Classroom ➕"):
            if new_class:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO classrooms (teacher_id, class_name) VALUES (?, ?)", (st.session_state.teacher_id, new_class))
                    conn.commit()
                    st.success(f"Private Classroom '{new_class}' created!")
                except sqlite3.IntegrityError:
                    st.error("Classroom name error!")

        # Load ONLY classrooms owned by logged in teacher
        classes_df = pd.read_sql("SELECT * FROM classrooms WHERE teacher_id = ?", conn, params=(st.session_state.teacher_id,))
        if not classes_df.empty:
            selected_class_name = st.selectbox("Select Active Private Classroom:", classes_df["class_name"].tolist())
            selected_class_row = classes_df[classes_df["class_name"] == selected_class_name].iloc[0]
            st.session_state.active_class_id = int(selected_class_row["id"])
            
            st.markdown("---")
            st.subheader(f"2. Add Students to '{selected_class_name}'")
            
            upload_type = st.radio("Student Input Method", ["CSV Upload", "Manual Entry"])
            if upload_type == "CSV Upload":
                up_file = st.file_uploader("Upload CSV (Columns: Roll_No, Name)", type=["csv"])
                if up_file and st.button("Save Students to Database"):
                    df_up = pd.read_csv(up_file)
                    df_up.columns = df_up.columns.str.strip().str.lower()
                    r_col = next((c for c in df_up.columns if "roll" in c), None)
                    n_col = next((c for c in df_up.columns if "name" in c), None)

                    if r_col and n_col:
                        for _, row in df_up.iterrows():
                            conn.execute("INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)", 
                                         (st.session_state.active_class_id, str(row[r_col]), str(row[n_col])))
                        conn.commit()
                        st.success("Uploaded and saved students into private classroom!")
                    else:
                        st.error("CSV must contain 'Roll_No' and 'Name' headers!")
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

            # Load Saved Groups
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
# TAB 2: SHARED QUESTION BANK DB & BULK CHECKBOXES
# ------------------------------------------
with tab_q_db:
    st.header("📚 Shared Question Bank DB (Contribute & Select)")
    conn = get_db_connection()

    col_q1, col_q2 = st.columns([1, 1.2])

    with col_q1:
        st.subheader("1. Add Question to Shared DB")
        q_topic = st.text_input("Topic Name:", value="Linear Algebra")
        q_text = st.text_area("Question Text (LaTeX Supported):", value=r"Eigenvalues of $A = \begin{bmatrix} 2 & 2 \\ 0 & 3 \end{bmatrix}$ are:")
        
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            op_a = st.text_input("Option A:", value=r"$\lambda_1 = 2, \lambda_2 = 3$")
            op_b = st.text_input("Option B:", value=r"$\lambda_1 = 0, \lambda_2 = 2$")
        with col_op2:
            op_c = st.text_input("Option C:", value=r"$\lambda_1 = 1, \lambda_2 = 3$")
            op_d = st.text_input("Option D:", value=r"$\lambda_1 = -2, \lambda_2 = -3$")

        correct_op = st.selectbox("Correct Option Index:", [0, 1, 2, 3], format_func=lambda x: f"Option {chr(65+x)}")

        if st.button("Contribute Question to Shared DB 💾"):
            conn.execute(
                "INSERT INTO question_bank (created_by, topic, question, option_labels, options, correct_idx) VALUES (?, ?, ?, ?, ?, ?)",
                (st.session_state.username, q_topic, q_text, json.dumps(["Option A", "Option B", "Option C", "Option D"]), json.dumps([op_a, op_b, op_c, op_d]), correct_op)
            )
            conn.commit()
            st.success("Question saved to shared database!")

    with col_q2:
        st.subheader("2. Select Individual/Bulk Questions for Quiz")
        q_bank_df = pd.read_sql("SELECT * FROM question_bank", conn)
        
        if not q_bank_df.empty:
            topics = ["All Topics"] + q_bank_df["topic"].unique().tolist()
            selected_topic = st.selectbox("Filter Question Bank by Topic:", topics)
            
            filtered_qs = q_bank_df if selected_topic == "All Topics" else q_bank_df[q_bank_df["topic"] == selected_topic]
            
            # Checkbox Selection System
            st.write("Select questions using checkboxes below:")
            selected_q_ids = []
            
            # Master Select All
            select_all = st.checkbox("Select All Filtered Questions")
            
            for _, row in filtered_qs.iterrows():
                is_selected = select_all or st.checkbox(f"[{row['topic']}] {row['question'][:60]}... (By: {row['created_by']})", key=f"q_{row['id']}")
                if is_selected:
                    selected_q_ids.append(row["id"])

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Import Selected Questions to Active Quiz 🚀"):
                    selected_rows = filtered_qs[filtered_qs["id"].isin(selected_q_ids)]
                    st.session_state.quiz_questions = []
                    for _, row in selected_rows.iterrows():
                        st.session_state.quiz_questions.append({
                            "question": row["question"],
                            "option_labels": json.loads(row["option_labels"]),
                            "options": json.loads(row["options"]),
                            "correct_idx": int(row["correct_idx"]),
                            "image_base64": row.get("image_base64")
                        })
                    st.session_state.current_q_idx = 0
                    st.success(f"Imported {len(selected_rows)} questions into active quiz session!")
            with col_btn2:
                if st.button("Import Entire Topic in Bulk 📦"):
                    st.session_state.quiz_questions = []
                    for _, row in filtered_qs.iterrows():
                        st.session_state.quiz_questions.append({
                            "question": row["question"],
                            "option_labels": json.loads(row["option_labels"]),
                            "options": json.loads(row["options"]),
                            "correct_idx": int(row["correct_idx"]),
                            "image_base64": row.get("image_base64")
                        })
                    st.session_state.current_q_idx = 0
                    st.success(f"Imported all {len(filtered_qs)} questions in bulk!")
        else:
            st.info("No questions stored in database yet.")

    conn.close()

# ------------------------------------------
# TAB 3: IMAGE/PDF QUIZ CREATOR
# ------------------------------------------
with tab_media_quiz:
    st.header("📷 Form Quiz via Images (JPG/PNG) or PDF Upload")
    st.markdown("Upload files, specify options/answers, and form a disposable/exportable quiz session.")

    uploaded_files = st.file_uploader("Upload Question Images or PDF", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        st.subheader("Define Options & Correct Answers for Uploaded Media")
        media_questions = []

        for idx, file in enumerate(uploaded_files):
            st.markdown(f"**Media Item {idx+1}: {file.name}**")
            
            # Read Image/PDF Bytes
            file_bytes = file.read()
            base64_str = base64.b64encode(file_bytes).decode("utf-8")
            
            col_m1, col_m2 = st.columns([1, 1])
            with col_m1:
                if file.type.startswith("image"):
                    st.image(file_bytes, use_container_width=True)
                elif file.type == "application/pdf":
                    st.info("📄 PDF File Uploaded.")

            with col_m2:
                q_title = st.text_input(f"Question Title/Prompt #{idx+1}:", value=f"Identify/Solve Question {idx+1}", key=f"media_q_{idx}")
                op_a = st.text_input("Option A:", value="Option A", key=f"med_a_{idx}")
                op_b = st.text_input("Option B:", value="Option B", key=f"med_b_{idx}")
                op_c = st.text_input("Option C:", value="Option C", key=f"med_c_{idx}")
                op_d = st.text_input("Option D:", value="Option D", key=f"med_d_{idx}")
                corr_i = st.selectbox("Correct Option:", [0, 1, 2, 3], format_func=lambda x: f"Option {chr(65+x)}", key=f"med_corr_{idx}")

                media_questions.append({
                    "question": q_title,
                    "option_labels": ["Option A", "Option B", "Option C", "Option D"],
                    "options": [op_a, op_b, op_c, op_d],
                    "correct_idx": corr_i,
                    "image_base64": base64_str if file.type.startswith("image") else None
                })
            st.markdown("---")

        if st.button("Form Quiz from Media Uploads 🚀"):
            st.session_state.quiz_questions = media_questions
            st.session_state.current_q_idx = 0
            st.success("Media quiz formed and loaded into active session!")

# ------------------------------------------
# TAB 4: LIVE CONTROL & DISCARD/DOWNLOAD QUIZ
# ------------------------------------------
with tab_portal:
    st.header("📲 Live Quiz Control & Management")

    # Quiz Export & Discard Management
    if st.session_state.quiz_questions:
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            # Download Full Quiz Data
            quiz_export_data = json.dumps(st.session_state.quiz_questions, indent=2)
            st.download_button(
                label="📥 Download Full Quiz (JSON)",
                data=quiz_export_data,
                file_name="full_quiz_export.json",
                mime="application/json"
            )
        with col_ex2:
            if st.button("🗑️ Discard Complete Quiz Session"):
                st.session_state.quiz_questions = []
                st.session_state.responses = []
                st.session_state.current_q_idx = 0
                st.success("Quiz completely discarded!")
                st.rerun()

    st.markdown("---")

    if not st.session_state.quiz_questions:
        st.warning("No active quiz running.")
    else:
        curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]

        # ENRICHED FONT SIZE & UNIFIED QUESTION AND OPTIONS BOX
        st.markdown(f"""
        <div class="unified-question-box">
            <h2>Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}</h2>
            <h3>{curr_q['question']}</h3>
            <hr style="border-color: #818CF8;">
            <p><strong>Option A:</strong> {curr_q['options'][0]}</p>
            <p><strong>Option B:</strong> {curr_q['options'][1]}</p>
            <p><strong>Option C:</strong> {curr_q['options'][2]}</p>
            <p><strong>Option D:</strong> {curr_q['options'][3]}</p>
        </div>
        """, unsafe_allow_html=True)

        if curr_q.get("image_base64"):
            st.image(f"data:image/png;base64,{curr_q['image_base64']}", width=400)

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

# ------------------------------------------
# TAB 5: ANALYTICS & INDIVIDUAL GROUP PIE CHARTS
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

    st.markdown(f"## 📊 Live Poll Analytics")
    
    if not st.session_state.quiz_questions:
        st.warning("No active quiz running.")
    else:
        df_resp = pd.DataFrame(st.session_state.responses)
        df_curr = df_resp[df_resp["Q_Idx"] == st.session_state.current_q_idx] if not df_resp.empty and "Q_Idx" in df_resp.columns else pd.DataFrame()
        
        if df_curr.empty:
            st.warning("Awaiting responses for current question...")
        else:
            curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]
            total_votes = len(df_curr)
            
            st.metric("Total Votes Received", total_votes)

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

            elif chart_type == "Individual Group Pie Charts":
                unique_groups = sorted(list(st.session_state.groups.keys()))
                if unique_groups:
                    cols = 2
                    rows = (len(unique_groups) + 1) // 2
                    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[f"Group: {g}" for g in unique_groups], specs=[[{"type": "domain"}]*cols]*rows)
                    
                    for idx, grp in enumerate(unique_groups):
                        r, c = (idx // cols) + 1, (idx % cols) + 1
                        grp_data = df_curr[df_curr["Group"] == grp]
                        pie_counts = grp_data["Label"].value_counts()
                        
                        fig.add_trace(go.Pie(labels=pie_counts.index, values=pie_counts.values, name=grp), row=r, col=c)
                    
                    fig.update_layout(template="plotly_dark", height=350 * rows)
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
