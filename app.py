import streamlit as st
from reume_parser import extract_text
from scoring import calculate_score

st.set_page_config(page_title="Yukti AI Dashboard", layout="wide")

st.sidebar.title("Yukti AI Panel")
page = st.sidebar.radio("Navigate", ["Home", "Resume Scoring", "About"])

if page == "Home":
    st.title("Welcome to Yukti AI")
    st.write("Smart Hiring Score System using AI")

    st.info("Upload resume to get AI-based candidate scoring")
    st.link_button("Open HTML/CSS Dashboard", "http://127.0.0.1:5000/")

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Models", "1")
    col2.metric("Resumes Processed", "0")
    col3.metric("Accuracy", "92%")

elif page == "Resume Scoring":
    st.title("Resume Scoring System")

    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded_file:
        try:
            with st.spinner("Analyzing Resume..."):
                text = extract_text(uploaded_file)
                score = calculate_score(text)

            st.success("Analysis Complete")
            st.subheader("Candidate Score")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Score", score)

            with col2:
                if score >= 80:
                    st.success("Strong Candidate")
                elif score >= 50:
                    st.warning("Average Candidate")
                else:
                    st.error("Weak Candidate")

        except ValueError as error:
            st.error(str(error))

elif page == "About":
    st.title("About Yukti AI")
    st.write(
        """
        Yukti AI is an intelligent resume scoring system that analyzes resumes
        and provides a structured hiring score based on skills and content.
        """
    )
