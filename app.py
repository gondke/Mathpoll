import json
import random
import sqlite3
import string
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="STEM Quiz System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .question-box {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SQLITE DATABASE ENGINE & HELPER FUNCTIONS
# ==========================================
DB_FILE = "quiz_system.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS classrooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_name TEXT UNIQUE NOT NULL
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id INTEGER,
                        roll_no TEXT NOT NULL,
                        name TEXT NOT NULL,
                        FOREIGN KEY(class_id) REFERENCES classrooms(id)
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS active_sessions (
                        session_code TEXT PRIMARY KEY,
                        class_id INTEGER,
                        FOREIGN KEY(class_id) REFERENCES classrooms(id)
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS student_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id INTEGER,
                        group_name TEXT NOT NULL,
                        roll_no TEXT NOT NULL,
                        FOREIGN KEY(class_id) REFERENCES classrooms(id)
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS question_bank (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        question TEXT NOT NULL,
                        option_labels TEXT NOT NULL,
                        options TEXT NOT NULL,
                        correct_idx INTEGER NOT NULL
                    )""")
        conn.commit()

init_db()

# Label Formatting Schemes
LABEL_FORMATS = {
    "Capital Letters (A, B, C, D)": ["A", "B", "C", "D"],
    "Small Letters (a, b, c, d)": ["a", "b", "c", "d"],
    "Numbers (1, 2, 3, 4)": ["1", "2", "3", "4"],
    "Small Roman (i, ii, iii, iv)": ["i", "ii", "iii", "iv"],
    "Capital Roman (I, II, III, IV)": ["I", "II", "III", "IV"],
    "Custom Options (Option 1, Option 2, ...)": ["Option 1", "Option 2", "Option 3", "Option 4"]
}

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "student_roll" not in st.session_state:
    st.session_state.student_roll = None

if "quiz_code" not in st.session_state:
    st.session_state.quiz_code = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )
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

def validate_session_code(code):
    clean_code = code.strip().upper()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT class_id FROM active_sessions WHERE session_code = ?", (clean_code,))
        row = c.fetchone()
        if row:
            return row[0]
    return None

# ==========================================
# 4. ENTRY / LOGIN SCREEN
# ==========================================
if st.session_state.user_role is None:
    st.title("🧪 STEM Live Quiz Portal")
    col_login, _ = st.columns([1.2, 1])

    with col_login:
        st.markdown("### Join Session")
        input_code = st.text_input(
            "Enter Session Code:", placeholder="e.g. A1B2C3"
        ).strip().upper()

        if input_code:
            matched_class_id = validate_session_code(input_code)
            
            if matched_class_id or (input_code == st.session_state.quiz_code and st.session_state.active_class_id):
                target_class_id = matched_class_id if matched_class_id else st.session_state.active_class_id
                st.session_state.active_class_id = target_class_id
                
                with get_db_connection() as conn:
                    students_df = pd.read_sql(
                        "SELECT roll_no, name FROM students WHERE class_id = ?",
                        conn,
                        params=(target_class_id,),
                    )

                if not students_df.empty:
                    student_options = (
                        students_df["roll_no"] + " - " + students_df["name"]
                    ).tolist()
                    selected_student = st.selectbox(
                        "Select Your Roll Number:", student_options
                    )
                    selected_roll = selected_student.split(" - ")[0]

                    if st.button("Join Class Quiz 🚀", use_container_width=True):
                        st.session_state.student_roll = selected_roll
                        st.session_state.user_role = "student"
                        st.rerun()
                else:
                    st.error("No enrolled students found for this session's class.")
            else:
                st.error("Invalid Session Code. Ensure the teacher has selected an active class.")

        st.markdown("---")
        with st.expander("Teacher / Host Access"):
            if st.button("Open Teacher Dashboard"):
                st.session_state.user_role = "teacher"
                st.rerun()

# ==========================================
# 5. STUDENT INTERFACE
# ==========================================
elif st.session_state.user_role == "student":
    st.title("📲 Student Quiz Interface")

    with get_db_connection() as conn:
        grps_df = pd.read_sql(
            "SELECT group_name, roll_no FROM student_groups WHERE class_id = ?",
            conn,
            params=(st.session_state.active_class_id,),
        )
        if not grps_df.empty:
            st.session_state.groups = grps_df.groupby("group_name")["roll_no"].apply(list).to_dict()

    assigned_group = "Unassigned"
    for grp, members in st.session_state.groups.items():
        if st.session_state.student_roll in members:
            assigned_group = grp
            break

    col_info1, col_info2 = st.columns(2)
    col_info1.info(f"**Roll Number:** {st.session_state.student_roll}")
    col_info2.success(f"**Group:** {assigned_group}")

    if not st.session_state.quiz_questions or st.session_state.current_q_idx >= len(st.session_state.quiz_questions):
        st.warning("Waiting for the teacher to broadcast questions...")
    elif st.session_state.quiz_ended:
        st.balloons()
        st.success("🎉 Quiz Completed! Please wait for the teacher to announce results.")
    else:
        curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]

        st.markdown(
            f"""
            <div class="question-box">
                <h4>Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}</h4>
                <h3>{curr_q['question']}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        choices = [
            f"{curr_q['option_labels'][i]}: {curr_q['options'][i]}"
            for i in range(len(curr_q["options"]))
        ]

        selected_idx = st.radio(
            "Choose your answer:",
            options=range(len(choices)),
            format_func=lambda x: choices[x],
        )

        if st.button("Submit Poll Answer 🚀", use_container_width=True):
            if assigned_group == "Unassigned":
                st.error("You are not assigned to a group yet. Contact your instructor.")
            else:
                st.session_state.responses = [
                    r for r in st.session_state.responses
                    if not (r["Q_Idx"] == st.session_state.current_q_idx and r["Roll_No"] == st.session_state.student_roll)
                ]
                st.session_state.responses.append({
                    "Q_Idx": st.session_state.current_q_idx,
                    "Roll_No": st.session_state.student_roll,
                    "Group": assigned_group,
                    "Option_Index": selected_idx,
                    "Label": curr_q["option_labels"][selected_idx],
                })
                st.success("Your response has been submitted!")

    st.markdown("---")
    if st.button("Leave Session"):
        st.session_state.user_role = None
        st.session_state.student_roll = None
        st.rerun()

# ==========================================
# 6. TEACHER DASHBOARD
# ==========================================
elif st.session_state.user_role == "teacher":
    st.sidebar.title("⚛️ Teacher Dashboard")

    if st.session_state.active_class_id:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO active_sessions (session_code, class_id) VALUES (?, ?)",
                (st.session_state.quiz_code, st.session_state.active_class_id),
            )
            conn.commit()

    st.sidebar.markdown(
        f"""
      <div style="background-color: #1F2937; border: 2px solid #3B82F6; border-radius: 12px; padding: 16px; text-align: center;">
          <span style="color: #9CA3AF; font-size: 0.9em;">Session Code</span><br>
          <span style="color: #60A5FA; font-weight: bold; font-size: 2em; letter-spacing: 3px;">{st.session_state.quiz_code}</span>
      </div>
      """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Logout Dashboard"):
        st.session_state.user_role = None
        st.rerun()

    st.title("🧪 STEM Live Quiz & Classroom Manager")

    tab_class_db, tab_q_db, tab_portal, tab_analytics = st.tabs([
        "🏫 Classroom & Group DB Manager",
        "📚 Topic-Wise Question Bank DB",
        "📲 Live Quiz Controller",
        "📺 Live Analytics & Leaderboard",
    ])

    # --- TAB 1: CLASSROOM DB ---
    with tab_class_db:
        st.header("🗄️ Classroom & Group Roster Database")
        col_c1, col_c2 = st.columns([1, 1])

        with get_db_connection() as conn:
            with col_c1:
                st.subheader("1. Manage Classrooms")
                new_class = st.text_input("New Classroom Name:")
                if st.button("Create Classroom ➕") and new_class:
                    try:
                        conn.execute(
                            "INSERT INTO classrooms (class_name) VALUES (?)", (new_class,)
                        )
                        conn.commit()
                        st.success(f"Classroom '{new_class}' created!")
                    except sqlite3.IntegrityError:
                        st.error("Classroom name already exists!")

                classes_df = pd.read_sql("SELECT * FROM classrooms", conn)
                if not classes_df.empty:
                    selected_class_name = st.selectbox(
                        "Select Active Classroom:", classes_df["class_name"].tolist()
                    )
                    selected_class_row = classes_df[
                        classes_df["class_name"] == selected_class_name
                    ].iloc[0]
                    st.session_state.active_class_id = int(selected_class_row["id"])

                    conn.execute(
                        "INSERT OR REPLACE INTO active_sessions (session_code, class_id) VALUES (?, ?)",
                        (st.session_state.quiz_code, st.session_state.active_class_id),
                    )
                    conn.commit()

                    st.markdown("---")
                    st.subheader("2. Add Students")
                    s_roll = st.text_input("Roll Number:")
                    s_name = st.text_input("Student Name:")
                    if st.button("Add Student"):
                        conn.execute(
                            "INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)",
                            (st.session_state.active_class_id, s_roll, s_name),
                        )
                        conn.commit()
                        st.success(f"Added {s_name}!")

            with col_c2:
                st.subheader("3. Classroom Roster & Groups")
                if st.session_state.active_class_id:
                    students_in_class = pd.read_sql(
                        "SELECT roll_no, name FROM students WHERE class_id = ?",
                        conn,
                        params=(st.session_state.active_class_id,),
                    )
                    st.dataframe(students_in_class, height=180, use_container_width=True)

                    num_g = st.number_input(
                        "Number of Groups", min_value=2, max_value=10, value=4
                    )
                    if st.button("Auto-Form Groups 🎲") and not students_in_class.empty:
                        conn.execute(
                            "DELETE FROM student_groups WHERE class_id = ?",
                            (st.session_state.active_class_id,),
                        )
                        shuffled_rolls = (
                            students_in_class["roll_no"].sample(frac=1).tolist()
                        )
                        st.session_state.groups = {}
                        for i in range(num_g):
                            grp_name = f"Group {chr(65 + i)}"
                            members = shuffled_rolls[i::num_g]
                            st.session_state.groups[grp_name] = members
                            for r_no in members:
                                conn.execute(
                                    "INSERT INTO student_groups (class_id, group_name, roll_no)"
                                    " VALUES (?, ?, ?)",
                                    (st.session_state.active_class_id, grp_name, r_no),
                                )
                        conn.commit()
                        st.success(f"Formed {num_g} groups!")

    # --- TAB 2: TOPIC-WISE QUESTION BANK DB ---
    with tab_q_db:
        st.header("📚 Topic-Wise Question Bank Database")
        with get_db_connection() as conn:
            col_q1, col_q2 = st.columns([1, 1.2])

            with col_q1:
                st.subheader("1. Add Question to Database")
                q_topic = st.text_input("Topic Name:", value="Linear Algebra")
                q_text = st.text_area("Question Text:", value=r"Eigenvalues of matrix $A$ are:")

                # UPDATE 2: Custom Option Label Format
                fmt_choice = st.selectbox(
                    "Select Option Labeling Style:",
                    list(LABEL_FORMATS.keys())
                )
                selected_labels = LABEL_FORMATS[fmt_choice]

                col_op1, col_op2 = st.columns(2)
                with col_op1:
                    op_a = st.text_input(f"{selected_labels[0]}:", value=r"$\lambda_1 = 2, \lambda_2 = 3$")
                    op_b = st.text_input(f"{selected_labels[1]}:", value=r"$\lambda_1 = 0, \lambda_2 = 2$")
                with col_op2:
                    op_c = st.text_input(f"{selected_labels[2]}:", value=r"$\lambda_1 = 1, \lambda_2 = 3$")
                    op_d = st.text_input(f"{selected_labels[3]}:", value=r"$\lambda_1 = -2, \lambda_2 = -3$")

                correct_op = st.selectbox(
                    "Correct Option:",
                    [0, 1, 2, 3],
                    format_func=lambda x: f"{selected_labels[x]}"
                )

                if st.button("Save Question to Bank 💾", use_container_width=True):
                    conn.execute(
                        "INSERT INTO question_bank (topic, question, option_labels, options, correct_idx) VALUES (?, ?, ?, ?, ?)",
                        (
                            q_topic,
                            q_text,
                            json.dumps(selected_labels),
                            json.dumps([op_a, op_b, op_c, op_d]),
                            correct_op,
                        ),
                    )
                    conn.commit()
                    st.success("Question saved to database!")

            with col_q2:
                st.subheader("2. Filter & Select Questions for Live Quiz")
                q_bank_df = pd.read_sql("SELECT * FROM question_bank", conn)

                if not q_bank_df.empty:
                    # UPDATE 3: Filter by Topic
                    all_topics = ["All Topics"] + q_bank_df["topic"].unique().tolist()
                    selected_topic = st.selectbox("Filter Question Bank by Topic:", all_topics)

                    if selected_topic != "All Topics":
                        filtered_qs = q_bank_df[q_bank_df["topic"] == selected_topic].copy()
                    else:
                        filtered_qs = q_bank_df.copy()

                    st.markdown(f"**Found {len(filtered_qs)} Questions**")

                    # UPDATE 1: Add Checkboxes via Data Editor
                    filtered_qs.insert(0, "Select", False)
                    
                    edited_df = st.data_editor(
                        filtered_qs[["Select", "id", "topic", "question"]],
                        column_config={
                            "Select": st.column_config.CheckboxColumn(
                                "Include in Quiz?",
                                default=False,
                            ),
                            "id": "Q_ID",
                            "topic": "Topic",
                            "question": "Question Text"
                        },
                        disabled=["id", "topic", "question"],
                        hide_index=True,
                        use_container_width=True,
                        height=280
                    )

                    selected_ids = edited_df[edited_df["Select"] == True]["id"].tolist()

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Import Selected Questions 🚀", use_container_width=True):
                            if not selected_ids:
                                st.warning("Please check at least one question checkbox above!")
                            else:
                                st.session_state.quiz_questions = []
                                selected_rows = q_bank_df[q_bank_df["id"].isin(selected_ids)]
                                for _, row in selected_rows.iterrows():
                                    st.session_state.quiz_questions.append({
                                        "question": row["question"],
                                        "option_labels": json.loads(row["option_labels"]),
                                        "options": json.loads(row["options"]),
                                        "correct_idx": int(row["correct_idx"]),
                                    })
                                st.session_state.current_q_idx = 0
                                st.session_state.responses = []
                                st.success(f"Imported {len(selected_ids)} questions to active quiz!")

                    with col_btn2:
                        if st.button("Import All Filtered Questions 📚", use_container_width=True):
                            st.session_state.quiz_questions = []
                            for _, row in filtered_qs.iterrows():
                                st.session_state.quiz_questions.append({
                                    "question": row["question"],
                                    "option_labels": json.loads(row["option_labels"]),
                                    "options": json.loads(row["options"]),
                                    "correct_idx": int(row["correct_idx"]),
                                })
                            st.session_state.current_q_idx = 0
                            st.session_state.responses = []
                            st.success(f"Imported all {len(filtered_qs)} filtered questions!")

                else:
                    st.info("No questions stored in database yet.")

    # --- TAB 3: CONTROLLER ---
    with tab_portal:
        st.header("🎮 Live Quiz Controller")
        if not st.session_state.quiz_questions:
            st.warning("Import questions from the Question Bank tab.")
        else:
            curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]
            st.markdown(
                f"### Active Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}"
            )
            st.markdown(f"**{curr_q['question']}**")

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
                if st.button("🏆 End Quiz"):
                    st.session_state.quiz_ended = True
                    st.rerun()

    # --- TAB 4: ANALYTICS ---
    with tab_analytics:
        st.header("📊 Live Poll Analytics")
        df_resp = pd.DataFrame(st.session_state.responses)
        if not df_resp.empty:
            df_curr = df_resp[df_resp["Q_Idx"] == st.session_state.current_q_idx]
            if not df_curr.empty:
                fig = px.histogram(
                    df_curr,
                    x="Group",
                    color="Label",
                    barmode="group",
                    template="plotly_dark",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No responses for this question yet.")
        else:
            st.info("No responses recorded yet.")
