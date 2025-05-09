import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

import uuid # For generating unique conversation IDs

load_dotenv()


# Point to the local server setup using LM Studio
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
    
)

# Initialize session state variables for multi-chat
if "conversations" not in st.session_state:
    st.session_state.conversations = {}  # Stores all conversations {id: {"title": "...", "messages": [...]}}
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "new_chat_trigger" not in st.session_state: # To help manage focus on new chat
    st.session_state.new_chat_trigger = False
    
# --- Sidebar for New Chat and Conversation History ---
with st.sidebar:
    st.title("Llama-3 Chat")
    st.caption("Powered by LM Studio")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_conv_id = str(uuid.uuid4())
        st.session_state.conversations[new_conv_id] = {
            "title": f"New Chat ({len(st.session_state.conversations) + 1})",
            "messages": []
        }
        st.session_state.current_conversation_id = new_conv_id
        st.session_state.new_chat_trigger = True # Signal that a new chat was just created
        st.rerun()

    st.write("---")
    st.subheader("Conversations")
    
    # Display conversation list, sorted by creation (implicitly, as dicts are ordered in Python 3.7+)
    # For explicit sorting by time, you'd need to store timestamps.
    # Display in reverse order of creation (newest first)
    conv_ids = list(st.session_state.conversations.keys())
    for conv_id in reversed(conv_ids):
        conv_title = st.session_state.conversations[conv_id]["title"]
        if st.button(conv_title, key=f"conv_btn_{conv_id}", use_container_width=True,
                      type="secondary" if st.session_state.current_conversation_id != conv_id else "primary"):
            st.session_state.current_conversation_id = conv_id
            st.session_state.new_chat_trigger = False # Not a newly created chat
            st.rerun()
            
# --- Main Chat Interface ---
if not st.session_state.current_conversation_id:
    # Initial screen - like ChatGPT's welcome
    st.markdown("<h1 style='text-align: center;'>ChatGPT Clone 🦙</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Chat with locally hosted Llama-3 using LM Studio 💯</p>", unsafe_allow_html=True)
    
    st.subheader("Start a new chat from the sidebar or try an example:")
    cols = st.columns(2)
    example_prompts = [
        "Explain quantum computing in simple terms",
        "Got any creative ideas for a 10 year old’s birthday?",
        "How do I make an HTTP request in Python?",
        "What is the capital of France?"
    ]
    for i, example_prompt in enumerate(example_prompts):
        if i < 2:
            with cols[0]:
                if st.button(example_prompt, key=f"ex_prompt_{i}", use_container_width=True):
                    # Create a new chat and pre-fill with this prompt
                    new_conv_id = str(uuid.uuid4())
                    st.session_state.conversations[new_conv_id] = {
                        "title": example_prompt[:30] + "..." if len(example_prompt) > 30 else example_prompt,
                        "messages": [{"role": "user", "content": example_prompt}]
                    }
                    st.session_state.current_conversation_id = new_conv_id
                    st.session_state.new_chat_trigger = True
                    st.rerun() # Will trigger API call in the main chat logic
        else:
            with cols[1]:
                if st.button(example_prompt, key=f"ex_prompt_{i}", use_container_width=True):
                    new_conv_id = str(uuid.uuid4())
                    st.session_state.conversations[new_conv_id] = {
                        "title": example_prompt[:30] + "..." if len(example_prompt) > 30 else example_prompt,
                        "messages": [{"role": "user", "content": example_prompt}]
                    }
                    st.session_state.current_conversation_id = new_conv_id
                    st.session_state.new_chat_trigger = True
                    st.rerun()
else:
    # Active chat selected
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
    
    # Display chat messages for the current conversation
    for message in current_conv["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            
   # Chat input
    if prompt := st.chat_input("Send a message..."):
        current_conv["messages"].append({"role": "user", "content": prompt})
        
        if len(current_conv["messages"]) == 1 and current_conv["title"].startswith("New Chat"): # Only first user message updates title
            title_candidate = prompt[:40] + "..." if len(prompt) > 40 else prompt
            st.session_state.conversations[st.session_state.current_conversation_id]["title"] = title_candidate

        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                api_messages = [{"role": m["role"], "content": m["content"]} for m in current_conv["messages"]]
                response = client.chat.completions.create(
                    model=os.environ.get("GROQ_API_KEY"), # Ensure this matches model in LM Studio
                    messages=api_messages,
                    temperature=0.7,
                    stream=False, # Streaming can be added for a more dynamic feel
                )
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
        
        current_conv["messages"].append({"role": "assistant", "content": assistant_response})
        st.session_state.new_chat_trigger = False # Reset trigger
        st.rerun() # Rerun to update sidebar title if changed, and reflect new messages

    # If it's a new chat that was just triggered by an example or "New Chat" button
    # and it's the user's turn (i.e., only one message from user, or empty)
    # and an example prompt was used (which means messages list is not empty)
    if st.session_state.new_chat_trigger and current_conv["messages"] and current_conv["messages"][-1]["role"] == "user":
        # This logic is to auto-send the first message if it came from an example prompt button
        with st.chat_message("user"): # Re-display user message from example
            st.markdown(current_conv["messages"][-1]["content"])

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                api_messages = [{"role": m["role"], "content": m["content"]} for m in current_conv["messages"]]
                response = client.chat.completions.create(
                    model=os.environ.get("GROQ_API_KEY"),
                    messages=api_messages,
                    temperature=0.7,
                )
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
        
        current_conv["messages"].append({"role": "assistant", "content": assistant_response})
        st.session_state.new_chat_trigger = False # Reset trigger
        st.rerun()
