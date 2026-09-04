f = filtered_doc_df.copy()
                filtered_doc_df.insert(0, "Select", False)

                edited_doc_df = st.data_editor(
                    filtered_doc_df[["Select", "id", "topic", "title", "file_name"]],
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Include?", default=False),
                        "id": "Doc_ID",
                        "topic": "Topic",
                        "title": "Title",
                        "file_name": "File Name",
                    },
                    disabled=["id", "topic", "title", "file_name"],
                    hide_index=True,
                    use_container_width=True,
                    height=280,
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
                        st.success(f"Loaded {len(docs_df)} document/image questions into projection!")

            else:
                st.info("No document/image questions stored in database yet.")

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

            # Styled Question Box Projection
            st.markdown(
                f"""
                <div class="question-box">
                    <span style="color: #A5B4FC; font-weight: bold; font-size: 1.1em;">TOPIC: {q_data['topic']}</span>
                    <h2 style="color: #FFFFFF; margin-top: 10px;">{q_data['question']}</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Display Options in Grid
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

            # Controls
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

            # Display File
            if "image" in file_type or d_data["file_name"].lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_bytes, use_column_width=True)
            elif "pdf" in file_type or d_data["file_name"].lower().endswith(".pdf"):
                base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.warning("Unsupported preview format.")

            if st.session_state.doc_show_answer:
                st.info(f"**Answer Key / Solution Note:** {d_data['answer_key']}")

            # Controls
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
