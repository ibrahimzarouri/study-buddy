import os

import streamlit as st
from dotenv import load_dotenv

from agent.study_agent import StudyBuddyAgent
from tools.document_loader import load_document
from tools.rag import RAGIndex

load_dotenv()

st.set_page_config(page_title="StudyBuddy", page_icon="📚", layout="wide")

# ── Session state ─────────────────────────────────────────────────────────────

for _k, _v in {
    "agent": None,
    "topics": [],
    "conversation": [],
    "app_state": "upload",   # upload | topic_select | questioning | feedback
    "last_filename": None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _load_file(uploaded_file):
    text = load_document(uploaded_file, uploaded_file.name)
    if len(text.strip()) < 50:
        raise ValueError("Document appears empty or could not be parsed.")
    rag = RAGIndex(text)
    agent = StudyBuddyAgent(text, rag)
    topics = agent.extract_topics()
    st.session_state.agent = agent
    st.session_state.topics = topics
    st.session_state.conversation = []
    st.session_state.app_state = "topic_select"
    st.session_state.last_filename = uploaded_file.name
    return len(text), topics


def _select_topic(topic: str):
    agent: StudyBuddyAgent = st.session_state.agent
    question = agent.start_topic(topic)
    st.session_state.conversation = [
        {
            "role": "buddy",
            "content": f"Let's explore **{topic}**. Try to explain the concepts in your own words — I'll give you feedback and dig deeper with follow-up questions.",
            "type": "intro",
        },
        {"role": "buddy", "content": question, "type": "question"},
    ]
    st.session_state.app_state = "questioning"


def _render_conversation():
    for msg in st.session_state.conversation:
        if msg["role"] == "buddy":
            with st.chat_message("assistant", avatar="🤖"):
                t = msg["type"]
                if t == "question":
                    st.markdown(f"**{msg['content']}**")
                elif t == "intro":
                    st.info(msg["content"])
                elif t == "feedback":
                    score = msg.get("score", "partial")
                    if score == "correct":
                        st.success(msg["content"])
                    elif score == "partial":
                        st.warning(msg["content"])
                    else:
                        st.error(msg["content"])
        else:
            with st.chat_message("user", avatar="🎓"):
                st.markdown(msg["content"])


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📚 StudyBuddy")
    st.caption("AI Learning Partner")
    st.divider()

    uploaded = st.file_uploader(
        "Upload lecture material",
        type=["pdf", "txt", "docx"],
        help="Supports PDF, plain text, and Word documents",
    )

    if uploaded and uploaded.name != st.session_state.last_filename:
        with st.spinner("Processing document…"):
            try:
                chars, topics = _load_file(uploaded)
                st.success(f"Loaded {chars:,} characters · {len(topics)} topics found")
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.last_filename = None

    if st.session_state.topics:
        st.divider()
        st.subheader("Topics")
        for topic in st.session_state.topics:
            if st.button(topic, key=f"btn_{topic}", use_container_width=True):
                with st.spinner("Preparing first question…"):
                    _select_topic(topic)
                st.rerun()

    st.divider()
    st.caption(f"Model: {os.getenv('MODEL', 'not configured')}")


# ── Main ──────────────────────────────────────────────────────────────────────

st.title("StudyBuddy — AI Learning Partner")

state = st.session_state.app_state

if state == "upload":
    st.info("Upload a PDF, TXT, or DOCX file in the sidebar to get started.")
    st.markdown("""
**How it works:**

1. Upload your lecture notes or slides (PDF, Word, or plain text)
2. StudyBuddy extracts the main topics automatically
3. Select a topic — StudyBuddy asks you a question **from the material only**
4. Explain the concept in your own words
5. Get instant feedback and targeted follow-up questions until the topic is mastered
""")

elif state == "topic_select":
    st.info("Document loaded. Select a topic from the sidebar to start a session.")
    if st.session_state.topics:
        st.subheader("Detected topics:")
        for t in st.session_state.topics:
            st.markdown(f"- {t}")

elif state in ("questioning", "feedback"):
    _render_conversation()

    if state == "questioning":
        answer = st.chat_input("Explain your understanding…")
        if answer:
            st.session_state.conversation.append(
                {"role": "student", "content": answer, "type": "answer"}
            )
            with st.spinner("Evaluating your answer…"):
                result = st.session_state.agent.evaluate_answer(answer)

            score = result.get("score", "partial")
            feedback = result.get("feedback", "")
            follow_up = result.get("follow_up")

            if score == "correct":
                st.session_state.conversation.append(
                    {
                        "role": "buddy",
                        "content": f"Correct! {feedback}",
                        "type": "feedback",
                        "score": "correct",
                    }
                )
                st.session_state.app_state = "feedback"

            elif follow_up:
                st.session_state.conversation.append(
                    {"role": "buddy", "content": feedback, "type": "feedback", "score": score}
                )
                st.session_state.conversation.append(
                    {"role": "buddy", "content": follow_up, "type": "question"}
                )
                # Stay in "questioning" — follow_up is now the active question

            else:
                # Max follow-ups reached or no follow-up generated
                st.session_state.conversation.append(
                    {
                        "role": "buddy",
                        "content": f"{feedback} Let's move on.",
                        "type": "feedback",
                        "score": score,
                    }
                )
                st.session_state.app_state = "feedback"

            st.rerun()

    elif state == "feedback":
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Next Question →", type="primary", use_container_width=True):
                with st.spinner("Generating next question…"):
                    q = st.session_state.agent.next_question()
                st.session_state.conversation.append(
                    {"role": "buddy", "content": q, "type": "question"}
                )
                st.session_state.app_state = "questioning"
                st.rerun()
        with col2:
            if st.button("Change Topic", use_container_width=True):
                st.session_state.conversation = []
                st.session_state.app_state = "topic_select"
                st.rerun()
        with col3:
            if st.button("Restart Topic", use_container_width=True):
                topic = st.session_state.agent.current_topic
                if topic:
                    with st.spinner("Restarting…"):
                        _select_topic(topic)
                st.rerun()
