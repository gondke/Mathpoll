import base64
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Set Page Config
st.set_page_config(page_title="STEM Quiz System", page_icon="🧪", layout="wide")

# Apply Dark Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .question-box {
        background-color: #1E293B;
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- DATABASE HELPERS ---
def get_db_connection():
    conn = sqlite3.connect("stem_quiz.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                question TEXT,
                opt_a TEXT, opt_b TEXT, opt_c TEXT, opt_d TEXT,
                correct_idx INTEGER
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pdf_jpg_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                title TEXT,
                file_name TEXT,
                file_type TEXT,
                file_bytes BLOB,
                answer_key TEXT
            )
        """
        )
        conn.commit()


init_db()

# --- INITIALIZE SESSION STATE ---
if "role" not in st.session_state:
    st.session_state.role = None
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "show_correct_answer" not in st.session_state:
    st.session_state.show_correct_answer = False
if "quiz_ended" not in st.session_state:
    st.session_state.quiz_ended = False
if "doc_questions" not in st.session_state:
    st.session_state.doc_questions = []
if "doc_current_idx" not in st.session_state:
    st.session_state.doc_current_idx = 0
if "doc_show_answer" not in st.session_state:
    st.session_state.doc_show_answer = False
if "responses" not in st.session_state:
    st.session_state.responses = []
if "session_code" not in st.session_state:
    st.session_state.session_code = "STEM123"

# --- SIDEBAR ROLE SELECTOR ---
st.sidebar.title("🧪 STEM Quiz Portal")
role = st.sidebar.radio("Select Portal Role:", ["Student", "Teacher"])

# ==========================================
# 🎓 STUDENT PORTAL
# ==========================================
if role == "Student":
    st.title("🎓 Student Live Quiz Portal")

    student_name = st.text_input("Enter Your Name:")
    roll_no = st.text_input("Enter Roll / Student ID:")
    group_name = st.text_input("Enter Group / Team Name:")
    input_code = st.text_input("Enter Session Code:")

    if input_code:
        if input_code.strip() != st.session_state.session_code:
            st.error("Invalid Session Code! Please check with your teacher.")
        elif st.session_state.quiz_ended:
            st.warning("This quiz has been ended by the teacher. Thank you for participating!")
        elif not st.session_state.quiz_questions:
            st.info("Connected! Waiting for teacher to start the quiz and load questions...")
        else:
            st.success("Successfully connected to live quiz session!")
            st.markdown("---")

            # Load active live question set by teacher
            q_idx = st.session_state.current_q_idx
            q_data = st.session_state.quiz_questions[q_idx]

            st.caption(f"Question {q_idx + 1} of {len(st.session_state.quiz_questions)}")

            # Display Question
            st.markdown(
                f"""
                <div class="question-box">
                    <span style="color: #A5B4FC; font-weight: bold; font-size: 1em;">TOPIC: {q_data['topic']}</span>
                    <h3 style="color: #FFFFFF; margin-top: 10px;">{q_data['question']}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Check if student already responded to this specific question
            has_responded = any(
                r["Roll_No"] == roll_no and r["Q_Idx"] == q_idx
                for r in st.session_state.responses
            )

            if has_responded:
                st.info("✅ You have submitted your answer for this question. Waiting for the next question...")
            else:
                st.write("**Select your answer:**")
                labels = q_data["option_labels"]
                opts = q_data["options"]

                # Render options selection form
                with st.form("student_answer_form"):
                    selected_option = st.radio(
                        "Options:",
                        options=range(len(opts)),
                        format_func=lambda idx: f"{labels[idx]}: {opts[idx]}",
                    )
                    submit_btn = st.form_submit_button("Submit Answer 🚀", use_container_width=True)

                    if submit_btn:
                        if not student_name or not roll_no or not group_name:
                            st.warning("Please fill in your Name, Roll Number, and Group before submitting!")
                        else:
                            # Record response
                            response_record = {
                                "Q_Idx": q_idx,
                                "Student_Name": student_name,
                                "Roll_No": roll_no,
                                "Group": group_name,
                                "Selected_Idx": selected_option,
                                "Label": labels[selected_option],
                                "Option_Text": opts[selected_option],
                                "Is_Correct": (selected_option == q_data["correct_idx"]),
                            }
                            st.session_state.responses.append(response_record)
                            st.success("Answer submitted successfully!")
                            st.rerun()

# ==========================================
# 👩‍🏫 TEACHER PORTAL
# ==========================================
else:
    st.title("👩‍🏫 Teacher Management Portal")

    st.sidebar.markdown("---")
    st.sidebar.text_input("Active Session Code:", value=st.session_state.session_code, disabled=True)

    tab_create, tab_load, tab_doc_load, tab_portal, tab_doc_portal, tab_analytics = st.tabs(
        [
            "📝 Create Questions",
            "📥 Import Quiz Questions",
            "📄 Import PDF/JPG Questions",
            "📺 Live Question Projection",
            "🖼️ Live Doc Projection",
            "📊 Analytics & Leaderboard",
        ]
    )

    # --- TAB 1: CREATE QUESTIONS ---
    with tab_create:
        st.header("Add New Question to Database")
        with st.form("add_q_form"):
            topic = st.text_input("Topic / Category")
            question = st.text_area("Question Statement")
            col_a, col_b = st.columns(2)
            with col_a:
                opt_a = st.text_input("Option A")
                opt_c = st.text_input("Option C")
            with col_b:
                opt_b = st.text_input("Option B")
                opt_d = st.text_input("Option D")

            correct_opt = st.selectbox("Correct Answer", ["Option A", "Option B", "Option C", "Option D"])
            submit = st.form_submit_button("Save Question to Bank")

            if submit:
                correct_idx = ["Option A", "Option B", "Option C", "Option D"].index(correct_opt)
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO question_bank (topic, question, opt_a, opt_b, opt_c, opt_d, correct_idx) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (topic, question, opt_a, opt_b, opt_c, opt_d, correct_idx),
                    )
                    conn.commit()
                st.success("Question saved successfully!")

    # --- TAB 2: IMPORT TEXT QUESTIONS TO LIVE QUIZ ---
    with tab_load:
        st.header("Select & Import Questions for Live Quiz")
        with get_db_connection() as conn:
            questions_df = pd.read_sql("SELECT * FROM question_bank", conn)

        if not questions_df.empty:
            questions_df.insert(0, "Select", False)
            edited_df = st.data_editor(
                questions_df[["Select", "id", "topic", "question"]],
                column_config={"Select": st.column_config.CheckboxColumn("Include?", default=False)},
                disabled=["id", "topic", "question"],
                hide_index=True,
                use_container_width=True,
            )

            selected_ids = edited_df[edited_df["Select"] == True]["id"].tolist()

            if st.button("Load Selected Questions to Live Quiz 🚀", use_container_width=True):
                if not selected_ids:
                    st.warning("Please select at least one question.")
                else:
                    selected_questions = questions_df[questions_df["id"].isin(selected_ids)].to_dict("records")
                    formatted_questions = []

                    for q in selected_questions:
                        formatted_questions.append(
                            {
                                "id": q["id"],
                                "topic": q["topic"],
                                "question": q["question"],
                                "options": [q["opt_a"], q["opt_b"], q["opt_c"], q["opt_d"]],
                                "option_labels": ["A", "B", "C", "D"],
                                "correct_idx": q["correct_idx"],
                            }
                        )

                    st.session_state.quiz_questions = formatted_questions
                    st.session_state.current_q_idx = 0
                    st.session_state.show_correct_answer = False
                    st.session_state.quiz_ended = False
                    st.session_state.responses = []
                    st.success(f"Loaded {len(formatted_questions)} questions into live session!")
        else:
            st.info("No questions found in database. Add questions in Tab 1 first.")

    # --- TAB 3: IMPORT PDF/JPG QUESTIONS ---
    with tab_doc_load:
        st.header("Upload Document / Image Questions")

        uploaded_file = st.file_uploader("Upload Question Image or PDF", type=["png", "jpg", "jpeg", "pdf"])
        doc_topic = st.text_input("Document Topic")
        doc_title = st.text_input("Document Title")
        doc_answer = st.text_area("Answer Key / Notes")

        if st.button("Save Document Question"):
            if uploaded_file and doc_title:
                file_bytes = uploaded_file.read()
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO pdf_jpg_questions (topic, title, file_name, file_type, file_bytes, answer_key) VALUES (?, ?, ?, ?, ?, ?)",
                        (doc_topic, doc_title, uploaded_file.name, uploaded_file.type, file_bytes, doc_answer),
                    )
                    conn.commit()
                st.success("Document question uploaded!")

        st.markdown("---")
        with get_db_connection() as conn:
            doc_df = pd.read_sql("SELECT id, topic, title, file_name FROM pdf_jpg_questions", conn)

        if not doc_df.empty:
            doc_df.insert(0, "Select", False)
            edited_doc_df = st.data_editor(
                doc_df,
                column_config={"Select": st.column_config.CheckboxColumn("Include?", default=False)},
                disabled=["id", "topic", "title", "file_name"],
                hide_index=True,
                use_container_width=True,
            )

            selected_doc_ids = edited_doc_df[edited_doc_df["Select"] == True]["id"].tolist()

            if st.button("Load Selected Document Questions 🖼️", use_container_width=True):
                if not selected_doc_ids:
                    st.warning("Select at least one document question!")
                else:
                    with get_db_connection() as conn:
                        placeholders = ",".join(["?"] * len(selected_doc_ids))
                        query = f"SELECT * FROM pdf_jpg_questions WHERE id IN ({placeholders})"
                        docs_df = pd.read_sql(query, conn, params=selected_doc_ids)

                    st.session_state.doc_questions = docs_df.to_dict("records")
                    st.session_state.doc_current_idx = 0
                    st.session_state.doc_show_answer = False
                    st.success(f"Loaded {len(docs_df)} document questions into projection!")

    # --- TAB 4: LIVE CLASSROOM PROJECTION DISPLAY ---
    with tab_portal:
        st.header("📺 Live Classroom Projection Display")

        if not st.session_state.quiz_questions:
            st.info("No text-based questions loaded. Go to Tab 2 to select and import questions.")
        else:
            q_idx = st.session_state.current_q_idx
            q_data = st.session_state.quiz_questions[q_idx]

            st.progress((q_idx + 1) / len(st.session_state.quiz_questions))
            st.caption(f"Question {q_idx + 1} of {len(st.session_state.quiz_questions)}")

            st.markdown(
                f"""
                <div class="question-box">
                    <span style="color: #A5B4FC; font-weight: bold; font-size: 1.1em;">TOPIC: {q_data['topic']}</span>
                    <h2 style="color: #FFFFFF; margin-top: 10px;">{q_data['question']}</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

            labels = q_data["option_labels"]
            opts = q_data["options"]
            c1, c2 = st.columns(2)
            cols = [c1, c2, c1, c2]

            for i in range(len(opts)):
                border_color = "#10B981" if (st.session_state.show_correct_answer and i == q_data["correct_idx"]) else "#475569"
                bg_color = "#064E3B" if (st.session_state.show_correct_answer and i == q_data["correct_idx"]) else "#1E293B"

                cols[i].markdown(
                    f"""
                    <div style="background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 12px; padding: 15px 20px; margin-bottom: 15px;">
                        <span style="color: #60A5FA; font-weight: bold; font-size: 1.2em;">{labels[i]}:</span>
                        <span style="color: #FFFFFF; font-size: 1.2em; margin-left: 10px;">{opts[i]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns(4)

            with ctrl_c1:
                if st.button("⬅️ Previous Question", disabled=(q_idx == 0), use_container_width=True):
                    st.session_state.current_q_idx -= 1
                    st.session_state.show_correct_answer = False
                    st.rerun()

            with ctrl_c2:
                if st.button("👁️ Reveal Answer", use_container_width=True):
                    st.session_state.show_correct_answer = not st.session_state.show_correct_answer
                    st.rerun()

            with ctrl_c3:
                if st.button("➡️ Next Question", disabled=(q_idx == len(st.session_state.quiz_questions) - 1), use_container_width=True):
                    st.session_state.current_q_idx += 1
                    st.session_state.show_correct_answer = False
                    st.rerun()

            with ctrl_c4:
                if st.button("🏁 End Live Quiz", type="primary", use_container_width=True):
                    st.session_state.quiz_ended = True
                    st.success("Quiz has been marked as completed for students.")

    # --- TAB 5: LIVE DOCUMENT/IMAGE QUIZ PROJECTION ---
    with tab_doc_portal:
        st.header("🖼️ Live Document & Image Question Projection")

        if not st.session_state.doc_questions:
            st.info("No document/image questions loaded. Go to Tab 3 to select and load files.")
        else:
            d_idx = st.session_state.doc_current_idx
            d_data = st.session_state.doc_questions[d_idx]

            st.caption(f"Document Question {d_idx + 1} of {len(st.session_state.doc_questions)}")
            st.subheader(f"[{d_data['topic']}] {d_data['title']}")

            file_bytes = d_data["file_bytes"]
            file_type = d_data["file_type"]

            if "image" in file_type or d_data["file_name"].lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_bytes, use_column_width=True)
            elif "pdf" in file_type or d_data["file_name"].lower().endswith(".pdf"):
                base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

            if st.session_state.doc_show_answer:
                st.info(f"**Answer Key / Solution Note:** {d_data['answer_key']}")

            st.markdown("---")
            dc1, dc2, dc3 = st.columns(3)

            with dc1:
                if st.button("⬅️ Prev Doc Question", disabled=(d_idx == 0), use_container_width=True):
                    st.session_state.doc_current_idx -= 1
                    st.session_state.doc_show_answer = False
                    st.rerun()

            with dc2:
                if st.button("👁️ Toggle Solution Key", use_container_width=True):
                    st.session_state.doc_show_answer = not st.session_state.doc_show_answer
                    st.rerun()

            with dc3:
                if st.button("➡️ Next Doc Question", disabled=(d_idx == len(st.session_state.doc_questions) - 1), use_container_width=True):
                    st.session_state.doc_current_idx += 1
                    st.session_state.doc_show_answer = False
                    st.rerun()

    # --- TAB 6: LIVE ANALYTICS & LEADERBOARD ---
    with tab_analytics:
        st.header("📊 Live Analytics & Group Leaderboard")

        if not st.session_state.responses:
            st.warning("No student responses collected yet.")
        else:
            df_resp = pd.DataFrame(st.session_state.responses)
            col_an1, col_an2 = st.columns(2)

            with col_an1:
                st.subheader("Current Question Response Distribution")
                curr_q_responses = df_resp[df_resp["Q_Idx"] == st.session_state.current_q_idx]

                if not curr_q_responses.empty:
                    fig_dist = px.bar(
                        curr_q_responses,
                        x="Label",
                        color="Group",
                        title=f"Responses for Question {st.session_state.current_q_idx + 1}",
                        barmode="stack",
                        template="plotly_dark",
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
                else:
                    st.info("No responses submitted for the active question yet.")

            with col_an2:
                st.subheader("Group Participation Summary")
                group_counts = df_resp.groupby("Group")["Roll_No"].nunique().reset_index()
                group_counts.columns = ["Group", "Active Students"]

                fig_part = px.pie(
                    group_counts,
                    names="Group",
                    values="Active Students",
                    title="Student Engagement by Group",
                    hole=0.4,
                    template="plotly_dark",
                )
                st.plotly_chart(fig_part, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 Response Audit Log")
            st.dataframe(df_resp, use_container_width=True)
