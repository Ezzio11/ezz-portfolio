import streamlit as st
import requests
from supabase import create_client
import time
import fitz
import numpy as np
from urllib.parse import quote
from PIL import Image
from io import BytesIO

# Supabase and OpenRouter configurations
OR_API_KEY = "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"
OR_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324:free"
PROJECT_URL = "https://gefqshdrgozkxdiuligl.supabase.co"
DB_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdlZnFzaGRyZ296a3hkaXVsaWdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NjgyNDMsImV4cCI6MjA1OTA0NDI0M30.QJbcNl479A5_tdq8lqNubMQS26fkwcPyk-zvTU0Ffy0"

supabase = create_client(PROJECT_URL, DB_API_KEY)

portfolio_faq = {
    "who are you": "I'm X.A.N.E. — Ezz Eldin Ahmed's assistant. He’s a statistics major passionate about data science, automation, and machine learning. He built me using Python, Streamlit, and Django.",
    "what do you do": "I support users by answering questions about Ezz Eldin’s work, skills, and projects. Think of me as a smart, interactive portfolio guide.",
    "skills": "Ezz is skilled in Python, R, SQL, statistical modeling, automation, and full-stack development with Streamlit and Django. He also works with Supabase, Excel, and Figma.",
    "projects": "His projects include a regression tool, time series forecaster, OCR scanner, AI chatbot (that’s me), and a custom platform replacing many third-party tools.",
    "tools": "He primarily uses Python, Streamlit, Django, and Supabase. He also works with Excel, R, and Figma — and is currently exploring Power BI.",
    "education": "Ezz studies Statistics and Economics at the Faculty of Economics and Political Science — blending theory, data, and real-world application.",
    "experience": "He’s coordinated a data science scholarship with EMAM, co-founded a research center, and led student-driven tools for learning and analytics.",
    "favorite project": "His favorite project is this portfolio — a central hub for his tools, chatbot, and regression models, all seamlessly embedded into one platform.",
    "what does xane stand for": "X.A.N.E. stands for: eXtended Artificial Neural Entity. I’m more than code — I’m a part of his creative process.",
    "how can i reach him": "You can reach Ezz via LinkedIn or the contact form on this website. He’s always open to opportunities and collaboration.",
    "can i see the source code": "Some projects are public on his GitHub, while others are private or under development. You can ask about a specific project.",
    "is this chatbot ai-powered": "Yes, partially. I’m built on a rule-based system with optional LLM integration for advanced answers and search tasks.",
    "what’s special about this site": "Unlike typical portfolios, this site is dynamic — combining tools, models, and a living assistant into one seamless interface.",
    "why streamlit": "Because it allows rapid, elegant development of interactive apps — perfect for building tools quickly without compromising UX.",
    "what’s next": "More ML engineering projects, improved explainability using SHAP/SHAPASH, and diving deeper into NLP and generative AI."
}

# Common functions
def chatbot(prompt):
    headers = {"Authorization": f"Bearer {OR_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": prompt}

    try:
        response = requests.post(OR_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return fallback_pollinations(prompt[-1]["content"])
    except Exception as e:
        st.error(f"OpenRouter error: {e}")
        return fallback_pollinations(prompt[-1]["content"])
    
def fallback_pollinations(message):
    try:
        fallback_url = f"https://text.pollinations.ai/{message}"
        response = requests.get(fallback_url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Pollinations also failed to respond. Please try again later."
    except Exception as e:
        return f"Text fallback failed: {e}"

def save_memory(chat_name, role, content):
    """Saves chat memory to the database."""
    data = {
        "chat_name": chat_name,
        "role": role,
        "content": content
    }
    supabase.table("chats").insert(data).execute()

def load_memory(chat_name):
    """Loads chat memory for a specific chat."""
    response = supabase.table("chats").select("*").eq("chat_name", chat_name).execute()
    return response.data

def load_all_memory():
    """Loads all chat sessions from the database."""
    response = supabase.table("chats").select("chat_name").execute()
    chat_names = {row['chat_name'] for row in response.data}
    chats = {name: load_memory(name) for name in chat_names}
    return chats if chats else {"Default": []}

def delete_chat(chat_name):
    """Deletes chat history from the database."""
    supabase.table("chats").delete().eq("chat_name", chat_name).execute()

def gradual_display(text, placeholder):
    """Displays text gradually."""
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text)
        time.sleep(0.0005)

def extract_pdf_text(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Page 1: Chatbot
def chatbot_page():
    st.sidebar.title("💬 Chats")

    if st.sidebar.button("🧹 Clear Current Chat"):
        delete_chat(st.session_state.current_chat)
        st.session_state.chat_sessions[st.session_state.current_chat] = []
        st.session_state.messages = []
        st.rerun()

    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = load_all_memory()
        if not st.session_state.chat_sessions:
            st.session_state.chat_sessions = {"Default": []}
    
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = "Default"
    
    chat_options = list(st.session_state.chat_sessions.keys()) + ["➕ New Chat"]
    selected_chat = st.sidebar.selectbox("Choose a chat:", chat_options)

    if selected_chat == "➕ New Chat":
        new_chat_name = st.sidebar.text_input("Enter chat name:")
        if st.sidebar.button("Create"):
            if new_chat_name and new_chat_name not in st.session_state.chat_sessions:
                st.session_state.chat_sessions[new_chat_name] = []
                st.session_state.current_chat = new_chat_name
                st.rerun()
    else:
        st.session_state.current_chat = selected_chat
    
    st.session_state.messages = st.session_state.chat_sessions[st.session_state.current_chat]

    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])   

    welcome = [
        "Greetings, warrior. Ready to unlock some secrets?",
        "Hello, I am XANE, your digital ninja assistant.",
        "Hey, apprentice. Ready to master the art of knowledge?",
        "XANE here. How can I assist you on your quest?",
        "Welcome, ninja. Let’s crack the code together.",
        "Hi there, ready to unleash your inner ninja?",
        "Step into the dojo. Ask anything, learn everything.",
        "XANE at your service. What’s your mission today?",
        "Greetings, young ninja. The path to insight awaits.",
        "Hey! Time to sharpen your skills and knowledge.",
        "Hello, ninja-in-training! How can I guide you?",
        "Welcome back, warrior. Let’s conquer your questions.",
        "Greetings from the digital dojo. What’s next on your path?",
        "Hey, warrior! Let’s hack through your toughest problems.",
        "Welcome, ninja master in the making. What’s your next move?"
    ]

    # Pick one randomly
    greeting = np.random.choice(welcome)

    # Display as header
    st.header(greeting)

    def send_message():
        chat_input = st.chat_input(
            "Ask me anything or upload files",
            key="chat_input",
            max_chars=None,
            accept_file="multiple",
            file_type=["jpg", "jpeg", "png", "pdf", "txt"],
            disabled=False
        )

        if chat_input:
            if chat_input.text and chat_input.text.strip():
                with st.chat_message("user"):
                    st.markdown(chat_input.text)
                
                save_memory(st.session_state.current_chat, "user", chat_input.text)
                st.session_state.messages.append({"role": "user", "content": chat_input.text})

            if chat_input.files:
                with st.chat_message("user"):
                    for uploaded_file in chat_input.files:
                        if uploaded_file.type.startswith('image/'):
                            st.image(uploaded_file)
                            file_content = f"![Uploaded Image]({uploaded_file.name})"

                        elif uploaded_file.type == "application/pdf":
                            try:
                                uploaded_file.seek(0)
                                text = extract_pdf_text(uploaded_file)
                                file_content = text
                                st.warning(f"PDF file uploaded: {uploaded_file.name}")
                            except Exception as e:
                                st.error(f"Failed to extract PDF text: {e}")
                                file_content = f"[PDF file: {uploaded_file.name}]"

                        elif uploaded_file.type == "text/plain":
                            try:
                                uploaded_file.seek(0)
                                text = uploaded_file.read().decode("utf-8")
                                file_content = text
                                st.warning(f"Text file uploaded: {uploaded_file.name}")
                            except Exception as e:
                                st.error(f"Failed to read text file: {e}")
                                file_content = f"[Text file: {uploaded_file.name}]"

                        else:
                            st.warning(f"Unsupported file type: {uploaded_file.type}")
                            continue
                        
                        save_memory(st.session_state.current_chat, "user", file_content)
                        st.session_state.messages.append({"role": "user", "content": file_content})

            response = ""
            if chat_input.text and isinstance(chat_input.text, str) and chat_input.text.strip():
                for question, answer in portfolio_faq.items():
                    if question.lower() in chat_input.text.lower():
                        response = answer
                        break

            if not response:
                with st.spinner("XANE is thinking... 🤖"):
                    response = chatbot(st.session_state.messages)

            st.session_state.messages.append({"role": "assistant", "content": response})
            save_memory(st.session_state.current_chat, "assistant", response)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                gradual_display(response, placeholder)
            
            st.session_state.chat_sessions[st.session_state.current_chat] = st.session_state.messages
        
    send_message()

# Page 2: Image Generator
def image_generator_page():
    st.title("🎨 Pollinations – Free Multi‑Model Generator")

    # Sidebar settings
    with st.sidebar:
        prompt = st.text_area("🖌️ Prompt", "Mass Effect Citadel scene at dusk", height=100)
        model = st.selectbox("⚙️ Model", ["flux", "flux-pro", "flux-cablyai", "turbo"])
        width = st.slider("Width", 512, 1536, 1024, 128)
        height = st.slider("Height", 512, 1536, 1024, 128)
        seed = st.number_input("Seed (optional)", value=42)

    # Generate button
    if st.button("✨ Generate Image"):
        if not prompt.strip():
            st.warning("Enter a prompt first.")
        else:
            prompt_enc = quote(prompt.strip())
            url = (
                f"https://image.pollinations.ai/prompt/{prompt_enc}"
                f"?model={model}&width={width}&height={height}&seed={seed}"
            )
            with st.spinner("Generating image..."):
                try:
                    resp = requests.get(url, timeout=60)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content))
                    st.image(img, caption=f"{model} – {width}×{height}", use_container_width=True)
                    st.download_button(
                        "📥 Download Image",
                        data=resp.content,
                        file_name=f"pollinations_{model}.jpg",
                        mime="image/jpeg"
                    )
                except Exception as e:
                    st.error(f"❌ Error generating image: {e}")

# Main app
def main():
    st.set_page_config("XANE - AI Assistant", layout="centered")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Chatbot", "Image Generator"])

    if page == "Chatbot":
        chatbot_page()
    elif page == "Image Generator":
        image_generator_page()

if __name__ == '__main__':
    main()