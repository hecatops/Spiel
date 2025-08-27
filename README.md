# 🎭 Spiel

**Spiel** is a lightweight, creative text adventure engine that turns your ideas into playable, choice-based stories — powered by LLMs and RAG. You give it a prompt, and it spins the tale.

Built with [Streamlit](https://streamlit.io) and [Groq](https://chat.groq.com) for simplicity, speed, and storytelling magic.

---

## ✨ Features

- 🧠 Powered by Llama-3.3-70B-Versatile via API (works with the free tier)
- 🎮 Interactive gameplay with clickable choices (no typing needed)
- 🖼 Minimalist UI, no setup fuss
- 🔐 Secure API key via Streamlit secrets

---

## 🚀 Get Started

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/spiel.git
cd spiel
pip install -r requirements.txt
```

### 2. Add Your Groq API Key
Replace API_KEY = st.secrets["API_KEY"] with
```bash
API_KEY = "YOUR_API_KEY"
```

### 3. Run the App
```bash
streamlit run spiel.py
```

Open http://localhost:8501 in your browser.
