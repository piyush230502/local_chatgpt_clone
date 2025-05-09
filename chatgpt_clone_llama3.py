import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import uuid


load_dotenv()


# Set up the Streamlit App
st.title("ChatGPT Clone using Llama-3 🦙")
st.caption("Chat with locally hosted Llama-3 using the LM Studio 💯")

# Point to the local server setup using LM Studio
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Generate response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=st.session_state.messages, temperature=0.7
    )
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.choices[0].message.content)




