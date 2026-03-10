from dotenv import load_dotenv
import os
from groq import Groq
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="AI Interview Coach", page_icon="🤖")




if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_counter" not in st.session_state:
    st.session_state.user_message_counter = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_completed" not in st.session_state:
    st.session_state.chat_completed = False
if "messages" not in st.session_state:
    st.session_state.messages = []


for key, val in {"name": "", "experience": "", "skills": "", 
                 "level": "Junior", "position": "Data Scientist", "company": "Amazon"}.items():
    if key not in st.session_state:
        st.session_state[key] = val

def complete_setup():
    st.session_state.setup_complete = True


if not st.session_state.setup_complete:
    st.title("Welcome to the Interview Prep Chatbot!")
    st.subheader("Personal information",divider="rainbow")
    
    st.session_state.name = st.text_input("Name", value=st.session_state.name)
    st.session_state.experience = st.text_input("Experience Level", value=st.session_state.experience)
    st.session_state.skills = st.text_input("Skills", value=st.session_state.skills)

    col1, col2 = st.columns(2)
    level_options = ["Junior", "Mid-level", "Senior"]
    pos_options = ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst","Web Developer", "Product Manager")
    comp_options = ("Amazon", "Meta", "Starlabs", "Nestle", "LinkedIn", "Spotify", "Gjirafa")

    with col1:
        st.session_state.level = st.radio("Level", options=level_options, 
                                          index=level_options.index(st.session_state.level))
    with col2:
        st.session_state.position = st.selectbox("Position", options=pos_options, 
                                                 index=pos_options.index(st.session_state.position))

    st.session_state.company = st.selectbox("Company", options=comp_options, 
                                            index=comp_options.index(st.session_state.company))

    st.button("Start Interview", on_click=complete_setup)


if st.session_state.setup_complete and not st.session_state.chat_completed and not st.session_state.feedback_shown:
    st.title(f"Interview at {st.session_state.company}")
    
    client = Groq(api_key=api_key)

    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "system",
            "content": f"You are an HR executive interviewing {st.session_state.name} for a {st.session_state.level} {st.session_state.position} role at {st.session_state.company}. Experience: {st.session_state.experience}. Skills: {st.session_state.skills}. Ask one concise question at a time."
        })
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})

   
if not st.session_state.feedback_shown:
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

if st.session_state.user_message_counter < 5 and not st.session_state.chat_completed and st.session_state.setup_complete:
    if user_input := st.chat_input("Your answer..."):

       
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.user_message_counter += 1

        with st.chat_message("user"):
            st.markdown(user_input)

        if st.session_state.user_message_counter < 5:

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                response_text = ""

                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        message_placeholder.markdown(response_text + "▌")

                message_placeholder.markdown(response_text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text
            })

        else:
            st.session_state.chat_completed = True
            st.rerun()  





if st.session_state.chat_completed and not st.session_state.feedback_shown:
    if st.button("Get Feedback"):
        st.session_state.feedback_shown = True
        st.rerun()

if st.session_state.feedback_shown:
    st.subheader("Feedback")
    feedback_client = Groq(api_key=api_key)
    
    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role'] != 'system'])
    
    with st.spinner("Generating feedback..."):
        res = feedback_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Provide a score 1-10 and feedback for this interview."},
                      {"role": "user", "content": history}]
        )
    st.markdown(res.choices[0].message.content)
    
    if st.button("Restart"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")