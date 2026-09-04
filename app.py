import base64
import json
import random
import sqlite3
import string
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    
    /* Student View Question Box */
    .question-box {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
        border: 2px solid #818CF8;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
    }

    /* Option Card Containers */
    .option-card-wrapper {
        background-color: #1E293B;
        border: 2px solid #475569;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
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
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

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
                        FOREIGN KEY(class_id) REFERENCES classrooms(id) ON DELETE CASCADE
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS active_sessions (
                        session_code TEXT PRIMARY KEY,
                        class_id INTEGER,
                        FOREIGN KEY(class_id) REFERENCES classrooms(id) ON DELETE CASCADE
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS student_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id INTEGER,
                        group_name TEXT NOT NULL,
                        roll_no TEXT NOT NULL,
                        FOREIGN KEY(class_id) REFERENCES classrooms(id) ON DELETE CASCADE
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS question_bank (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        question TEXT NOT NULL,
                        option_labels TEXT NOT NULL,
                        options TEXT NOT NULL,
                        correct_idx INTEGER NOT NULL
                    )""")
        c.execute("""CREATE TABLE IF NOT EXISTS pdf_jpg_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        title TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_bytes BLOB NOT NULL,
                        answer_key TEXT NOT NULL
                    )""")
        conn.commit()

init_db()

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
if "show_correct_answer" not in st.session_state:
    st.session_state.show_correct_answer = False

if "doc_questions" not in st.session_state:
    st.session_state.doc_questions = []
if "doc_current_idx" not in st.session_state:
    st.session_state.doc_current_idx = 0
if "doc_show_answer" not in st.session_state:
    st.session_state.doc_show_answer = False

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

        st.markdown(f"#### Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}")
        st.write(f"### {curr_q['question']}")

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

    tab_class_db, tab_q_db, tab_upload_db, tab_portal, tab_doc_portal, tab_analytics = st.tabs([
        "🏫 Classroom & Group DB Manager",
        "📚 Topic-Wise Question Bank DB",
        "📄 Upload & Manage Doc/Image Questions",
        "📺 Live Classroom Projection Display",
        "🖼️ Live Document/Image Quiz Projection",
        "📊 Live Analytics & Leaderboard",
    ])

    # --- TAB 1: CLASSROOM DB ---
    with tab_class_db:
        st.header("🗄️ Classroom & Group Roster Database")
        col_c1, col_c2 = st.columns([1, 1.2])

        with get_db_connection() as conn:
            with col_c1:
                st.subheader("1. Manage Classrooms")
                new_class = st.text_input("New Classroom Name:")
                if st.button("Create Classroom ➕") and new_class:
                    try:
                        conn.execute("INSERT INTO classrooms (class_name) VALUES (?)", (new_class,))
                        conn.commit()
                        st.success(f"Classroom '{new_class}' created!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Classroom name already exists!")

                classes_df = pd.read_sql("SELECT * FROM classrooms", conn)
                if not classes_df.empty:
                    selected_class_name = st.selectbox(
                        "Select Active Classroom:", classes_df["class_name"].tolist()
                    )
                    selected_class_row = classes_df[classes_df["class_name"] == selected_class_name].iloc[0]
                    st.session_state.active_class_id = int(selected_class_row["id"])

                    conn.execute(
                        "INSERT OR REPLACE INTO active_sessions (session_code, class_id) VALUES (?, ?)",
                        (st.session_state.quiz_code, st.session_state.active_class_id),
                    )
                    conn.commit()

                    if st.button("🗑️ Delete Current Classroom", type="primary"):
                        conn.execute("DELETE FROM classrooms WHERE id = ?", (st.session_state.active_class_id,))
                        conn.commit()
                        st.session_state.active_class_id = None
                        st.success(f"Classroom '{selected_class_name}' and all associated student data were deleted.")
                        st.rerun()

                    st.markdown("---")
                    st.subheader("2. Add Students to Selected Class")
                    
                    add_mode = st.radio("Student Registration Method:", ["Manual Single Entry", "CSV Upload"], horizontal=True)
                    
                    if add_mode == "Manual Single Entry":
                        s_roll = st.text_input("Roll Number:")
                        s_name = st.text_input("Student Name:")
                        if st.button("Add Student"):
                            if s_roll and s_name:
                                conn.execute(
                                    "INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)",
                                    (st.session_state.active_class_id, s_roll, s_name),
                                )
                                conn.commit()
                                st.success(f"Added {s_name} ({s_roll})!")
                                st.rerun()
                            else:
                                st.warning("Provide both roll number and name.")
                    else:
                        st.markdown("**Upload CSV file** with columns: `roll_no`, `name`")
                        csv_file = st.file_uploader("Upload Student Roster CSV", type=["csv"])
                        if csv_file is not None:
                            try:
                                df_upload = pd.read_csv(csv_file)
                                df_upload.columns = df_upload.columns.str.strip().str.lower()
                                if "roll_no" in df_upload.columns and "name" in df_upload.columns:
                                    added_count = 0
                                    for _, r in df_upload.iterrows():
                                        r_no = str(r["roll_no"]).strip()
                                        n_me = str(r["name"]).strip()
                                        if r_no and n_me:
                                            conn.execute(
                                                "INSERT INTO students (class_id, roll_no, name) VALUES (?, ?, ?)",
                                                (st.session_state.active_class_id, r_no, n_me),
                                            )
                                            added_count += 1
                                    conn.commit()
                                    st.success(f"Successfully imported {added_count} students from CSV!")
                                    st.rerun()
                                else:
                                    st.error("CSV must contain `roll_no` and `name` headers.")
                            except Exception as ex:
                                st.error(f"Error parsing CSV: {ex}")

            with col_c2:
                st.subheader("3. Classroom Roster & Group Formation")
                if st.session_state.active_class_id:
                    students_in_class = pd.read_sql(
                        "SELECT roll_no, name FROM students WHERE class_id = ?",
                        conn,
                        params=(st.session_state.active_class_id,),
                    )

                    if not students_in_class.empty:
                        existing_groups_df = pd.read_sql(
                            "SELECT group_name, roll_no FROM student_groups WHERE class_id = ?",
                            conn,
                            params=(st.session_state.active_class_id,),
                        )
                        if not existing_groups_df.empty:
                            st.markdown("**Current Group Assignments:**")
                            st.dataframe(
                                existing_groups_df.groupby("group_name")["roll_no"].apply(list).reset_index(),
                                use_container_width=True
                            )

                        group_method = st.radio("Group Formation Mode:", ["Manual Checkbox Selection", "Auto-Form Groups"], horizontal=True)

                        if group_method == "Auto-Form Groups":
                            num_g = st.number_input("Number of Groups", min_value=2, max_value=10, value=4)
                            if st.button("Auto-Form Groups 🎲"):
                                conn.execute("DELETE FROM student_groups WHERE class_id = ?", (st.session_state.active_class_id,))
                                shuffled_rolls = students_in_class["roll_no"].sample(frac=1).tolist()
                                st.session_state.groups = {}
                                for i in range(num_g):
                                    grp_name = f"Group {chr(65 + i)}"
                                    members = shuffled_rolls[i::num_g]
                                    st.session_state.groups[grp_name] = members
                                    for r_no in members:
                                        conn.execute(
                                            "INSERT INTO student_groups (class_id, group_name, roll_no) VALUES (?, ?, ?)",
                                            (st.session_state.active_class_id, grp_name, r_no),
                                        )
                                conn.commit()
                                st.success(f"Auto-formed {num_g} groups!")
                                st.rerun()

                        else:
                            st.markdown("**Enrolled Students Checkbox Selection:**")
                            st.caption("Tick the checkboxes next to the students you want to assign to a group.")
                            
                            students_editor_df = students_in_class.copy()
                            students_editor_df.insert(0, "Select", False)

                            edited_roster = st.data_editor(
                                students_editor_df,
                                column_config={
                                    "Select": st.column_config.CheckboxColumn(
                                        "Select",
                                        help="Tick to add to group",
                                        default=False,
                                    ),
                                    "roll_no": "Roll Number",
                                    "name": "Student Name",
                                },
                                disabled=["roll_no", "name"],
                                hide_index=True,
                                use_container_width=True,
                                height=250,
                            )

                            selected_rolls = edited_roster[edited_roster["Select"] == True]["roll_no"].astype(str).tolist()

                            col_mg1, col_mg2 = st.columns([1.5, 1])
                            with col_mg1:
                                manual_grp_name = st.text_input("Assign to Group Name:", value="Group A")
                            
                            col_m1, col_m2 = st.columns(2)
                            with col_m1:
                                if st.button("Save Selected to Group 💾", use_container_width=True):
                                    if manual_grp_name and selected_rolls:
                                        conn.execute(
                                            "DELETE FROM student_groups WHERE class_id = ? AND (group_name = ? OR roll_no IN ({}))".format(
                                                ",".join(["?"] * len(selected_rolls))
                                            ),
                                            [st.session_state.active_class_id, manual_grp_name] + selected_rolls,
                                        )
                                        for r_no in selected_rolls:
                                            conn.execute(
                                                "INSERT INTO student_groups (class_id, group_name, roll_no) VALUES (?, ?, ?)",
                                                (st.session_state.active_class_id, manual_grp_name, str(r_no)),
                                            )
                                        conn.commit()
                                        st.success(f"Assigned {len(selected_rolls)} student(s) to '{manual_grp_name}'!")
                                        st.rerun()
                                    else:
                                        st.warning("Ensure group name is given and at least one student checkbox is ticked.")
                            
                            with col_m2:
                                if st.button("Reset All Groups 🧹", use_container_width=True):
                                    conn.execute("DELETE FROM student_groups WHERE class_id = ?", (st.session_state.active_class_id,))
                                    conn.commit()
                                    st.success("Cleared all group assignments.")
                                    st.rerun()
                    else:
                        st.info("No students enrolled in this classroom yet.")

    # --- TAB 2: TOPIC-WISE QUESTION BANK DB ---
    with tab_q_db:
        st.header("📚 Topic-Wise Question Bank Database")
        with get_db_connection() as conn:
            col_q1, col_q2 = st.columns([1, 1.2])

            with col_q1:
                st.subheader("1. Add Question to Database")
                q_topic = st.text_input("Topic Name:", value="Differential Equations")
                q_text = st.text_area("Question Text:", value=r"Laplace Transform of $e^{3t}$ is:")

                fmt_choice = st.selectbox(
                    "Select Option Labeling Style:",
                    list(LABEL_FORMATS.keys())
                )
                selected_labels = LABEL_FORMATS[fmt_choice]

                col_op1, col_op2 = st.columns(2)
                with col_op1:
                    op_a = st.text_input(f"{selected_labels[0]}:", value=r"$\frac{1}{s+3}$")
                    op_b = st.text_input(f"{selected_labels[1]}:", value=r"$\frac{1}{s-3}$")
                with col_op2:
                    op_c = st.text_input(f"{selected_labels[2]}:", value=r"$\frac{s}{s-3}$")
                    op_d = st.text_input(f"{selected_labels[3]}:", value=r"$\frac{s}{s+3}$")

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
                    all_topics = ["All Topics"] + q_bank_df["topic"].unique().tolist()
                    selected_topic = st.selectbox("Filter Question Bank by Topic:", all_topics)

                    if selected_topic != "All Topics":
                        filtered_qs = q_bank_df[q_bank_df["topic"] == selected_topic].copy()
                    else:
                        filtered_qs = q_bank_df.copy()

                    st.markdown(f"**Found {len(filtered_qs)} Questions**")

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
                                        "topic": row["topic"],
                                        "question": row["question"],
                                        "option_labels": json.loads(row["option_labels"]),
                                        "options": json.loads(row["options"]),
                                        "correct_idx": int(row["correct_idx"]),
                                    })
                                st.session_state.current_q_idx = 0
                                st.session_state.responses = []
                                st.session_state.show_correct_answer = False
                                st.success(f"Imported {len(selected_ids)} questions to active quiz!")

                    with col_btn2:
                        if st.button("Import All Filtered Questions 📚", use_container_width=True):
                            st.session_state.quiz_questions = []
                            for _, row in filtered_qs.iterrows():
                                st.session_state.quiz_questions.append({
                                    "topic": row["topic"],
                                    "question": row["question"],
                                    "option_labels": json.loads(row["option_labels"]),
                                    "options": json.loads(row["options"]),
                                    "correct_idx": int(row["correct_idx"]),
                                })
                            st.session_state.current_q_idx = 0
                            st.session_state.responses = []
                            st.session_state.show_correct_answer = False
                            st.success(f"Imported all {len(filtered_qs)} filtered questions!")

                else:
                    st.info("No questions stored in database yet.")

    # --- TAB 3: UPLOAD & MANAGE DOC/IMAGE QUESTIONS ---
    with tab_upload_db:
        st.header("📄 Upload & Manage Document/Image Question Bank")
        
        col_up1, col_up2 = st.columns([1, 1.2])

        with col_up1:
            st.subheader("1. Upload Question File (PDF/JPG/PNG)")
            doc_topic = st.text_input("Question Topic:", value="Physics Mechanics", key="doc_topic_in")
            doc_title = st.text_input("Question Title/Identifier:", value="Q1 - Vector Diagram", key="doc_title_in")
            uploaded_file = st.file_uploader("Choose File", type=["jpg", "jpeg", "png", "pdf"])
            doc_answer_key = st.text_input("Answer Key / Solution Note:", value="Option B (9.8 m/s²)")

            if st.button("Save Uploaded Question 💾", use_container_width=True):
                if uploaded_file is not None:
                    file_bytes = uploaded_file.read()
                    file_type = uploaded_file.type
                    file_name = uploaded_file.name

                    with get_db_connection() as conn:
                        conn.execute(
                            "INSERT INTO pdf_jpg_questions (topic, title, file_name, file_type, file_bytes, answer_key) VALUES (?, ?, ?, ?, ?, ?)",
                            (doc_topic, doc_title, file_name, file_type, file_bytes, doc_answer_key),
                        )
                        conn.commit()
                    st.success(f"Successfully saved {file_name} into Document Question Bank!")
                    st.rerun()
                else:
                    st.error("Please upload a valid file first.")

        with col_up2:
            st.subheader("2. Filter & Select Document Questions for Live Session")
            with get_db_connection() as conn:
                doc_bank_df = pd.read_sql("SELECT id, topic, title, file_name, file_type, answer_key FROM pdf_jpg_questions", conn)

            if not doc_bank_df.empty:
                doc_topics = ["All Topics"] + doc_bank_df["topic"].unique().tolist()
                sel_doc_topic = st.selectbox("Filter Document Bank by Topic:", doc_topics)

                if sel_doc_topic != "All Topics":
                    filtered_doc_df = doc_bank_df[doc_bank_df["topic"] == sel_doc_topic].copy()
                else:
                    filtered_doc_df = doc_bank_df.copy()

                filtered_doc_df.insert(0, "Select", False)

                edited_doc_df = st.data_editor(
                    filtered_doc_df[["Select", "id", "topic", "title", "file_name"]],
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Include in Quiz?", default=False),
                        "id": "id",
                        "topic": "Topic",
                        "title": "Title",
                        "file_name": "File Name",
                    },
                    disabled=["id", "topic", "title", "file_name"],
                    hide_index=True,
                    use_container_width=True,
                    height=280
                )

                selected_doc_ids = edited_doc_df[edited_doc_df["Select"] == True]["id"].tolist()

                if st.button("Load Selected Questions to Live Projection 🚀", use_container_width=True):
                    if not selected_doc_ids:
                        st.warning("Please select at least one document question checkbox.")
                    else:
                        with get_db_connection() as conn:
                            query = f"SELECT * FROM pdf_jpg_questions WHERE id IN ({','.join(map(str, selected_doc_ids))})"
                            loaded_docs = pd.read_sql(query, conn)
                        
                        st.session_state.doc_questions = loaded_docs.to_dict(orient="records")
                        st.session_state.doc_current_idx = 0
                        st.session_state.doc_show_answer = False
                        st.success(f"Loaded {len(loaded_docs)} document/image questions for Live Quiz Projection!")
            else:
                st.info("No uploaded questions found in the document bank.")

    # --- TAB 4: LIVE CLASSROOM PROJECTION DISPLAY ---
    with tab_portal:
        st.header("📺 Live Classroom Projection Display")
        
        if not st.session_state.quiz_questions:
            st.warning("No questions loaded. Import questions from the Question Bank tab.")
        else:
            curr_q = st.session_state.quiz_questions[st.session_state.current_q_idx]
            q_topic = curr_q.get("topic", "General")
            correct_idx = curr_q.get("correct_idx", 0)
            
            with st.container(border=True):
                col_badge, col_count = st.columns([1, 1])
                with col_badge:
                    st.markdown(f"#### 📌 `{q_topic.upper()}`")
                with col_count:
                    st.markdown(f"<div style='text-align: right; color: #94A3B8; font-weight: bold; font-size: 1.2rem;'>Question {st.session_state.current_q_idx + 1} of {len(st.session_state.quiz_questions)}</div>", unsafe_allow_html=True)

                st.markdown("---")
                st.write(f"# {curr_q['question']}")
                st.markdown("---")

                col1, col2 = st.columns(2)
                for idx, (label, opt_text) in enumerate(zip(curr_q["option_labels"], curr_q["options"])):
                    target_col = col1 if idx % 2 == 0 else col2
                    is_correct = (idx == correct_idx) and st.session_state.show_correct_answer
                    
                    with target_col:
                        if is_correct:
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #064E3B;
                                    border: 3px solid #059669;
                                    border-radius: 12px;
                                    padding: 15px 20px;
                                    margin-bottom: 15px;
                                    box-shadow: 0 0 15px rgba(5, 150, 105, 0.4);
                                ">
                                    <h3 style="margin: 0; color: #34D399;">{label} (Correct Answer ✅)</h3>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.write(f"## {opt_text}")
                        else:
                            with st.container(border=True):
                                st.write(f"### **{label}**")
                                st.write(f"## {opt_text}")

            st.markdown("<br>", unsafe_allow_html=True)

            col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1.2, 1, 1])
            
            with col_nav1:
                if st.button("⬅️ Previous", use_container_width=True) and st.session_state.current_q_idx > 0:
                    st.session_state.current_q_idx -= 1
                    st.session_state.show_correct_answer = False
                    st.rerun()

            with col_nav2:
                btn_label = "🙈 Hide Correct Answer" if st.session_state.show_correct_answer else "👁️ Reveal Correct Answer"
                if st.button(btn_label, use_container_width=True):
                    st.session_state.show_correct_answer = not st.session_state.show_correct_answer
                    st.rerun()

            with col_nav3:
                if st.button("Next ➡️", use_container_width=True) and st.session_state.current_q_idx < len(st.session_state.quiz_questions) - 1:
                    st.session_state.current_q_idx += 1
                    st.session_state.show_correct_answer = False
                    st.rerun()

            with col_nav4:
                if st.button("🏆 End Quiz", use_container_width=True):
                    st.session_state.quiz_ended = True
                    st.rerun()

    # --- TAB 5: LIVE DOCUMENT / IMAGE QUIZ PROJECTION ---
    with tab_doc_portal:
        st.header("🖼️ Live Document / Image Quiz Projection Display")

        if not st.session_state.doc_questions:
            st.warning("No Document/Image questions loaded. Please select and load them from '📄 Upload & Manage Doc/Image Questions' tab.")
        else:
            curr_doc = st.session_state.doc_questions[st.session_state.doc_current_idx]
            
            with st.container(border=True):
                col_d_badge, col_d_count = st.columns([1, 1])
                with col_d_badge:
                    st.markdown(f"#### 📌 `{curr_doc['topic'].upper()}` - {curr_doc['title']}")
                with col_d_count:
                    st.markdown(
                        f"<div style='text-align: right; color: #94A3B8; font-weight: bold; font-size: 1.2rem;'>"
                        f"Question {st.session_state.doc_current_idx + 1} of {len(st.session_state.doc_questions)}</div>",
                        unsafe_allow_html=True
                    )

                st.markdown("---")

                file_bytes = curr_doc["file_bytes"]
                file_type = curr_doc["file_type"]

                if "pdf" in file_type.lower():
                    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.image(file_bytes, use_container_width=True)

                st.markdown("---")

                if st.session_state.doc_show_answer:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #064E3B;
                            border: 3px solid #059669;
                            border-radius: 12px;
                            padding: 20px;
                            margin-top: 10px;
                            box-shadow: 0 0 15px rgba(5, 150, 105, 0.4);
                        ">
                            <h3 style="margin: 0; color: #34D399;">✅ Correct Solution / Answer Key:</h3>
                            <h2 style="margin-top: 5px; color: #FFFFFF;">{curr_doc['answer_key']}</h2>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            col_d_nav1, col_d_nav2, col_d_nav3 = st.columns([1, 1.2, 1])

            with col_d_nav1:
                if st.button("⬅️ Previous Doc Question", use_container_width=True) and st.session_state.doc_current_idx > 0:
                    st.session_state.doc_current_idx -= 1
                    st.session_state.doc_show_answer = False
                    st.rerun()

            with col_d_nav2:
                doc_btn_label = "🙈 Hide Answer Key" if st.session_state.doc_show_answer else "👁️ Reveal Answer Key"
                if st.button(doc_btn_label, use_container_width=True):
                    st.session_state.doc_show_answer = not st.session_state.doc_show_answer
                    st.rerun()

            with col_d_nav3:
                if st.button("Next Doc Question ➡️", use_container_width=True) and st.session_state.doc_current_idx < len(st.session_state.doc_questions) - 1:
                    st.session_state.doc_current_idx += 1
                    st.session_state.doc_show_answer = False
                    st.rerun()

    # --- TAB 6: ANALYTICS ---
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
