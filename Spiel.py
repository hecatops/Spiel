import streamlit as st
import requests
import logging
import re
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "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"
MODEL_NAME = "llama-3.3-70b-versatile"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

banned_words = [
    "whore", "fuck", "shit", "bitch", "cunt", "dick", "cock", "pussy", "penis", "vagina",
    "asshole", "rape", "molest", "porn", "prostitute", "whorehouse", "orgy", "slut",
    "masturbate", "fetish", "erotic", "xxx", "nude", "nudity"
]

def is_safe(text):
    clean_text = re.sub(r'[^a-zA-Z]', '', text.lower())
    for word in banned_words:
        if word in clean_text:
            return False
    return True

# Initialize session state
def initialize_session_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""
    if "original_setting" not in st.session_state:
        st.session_state.original_setting = ""
    if "start" not in st.session_state:
        st.session_state.start = False
    if "choice_count" not in st.session_state:
        st.session_state.choice_count = 0
    if "story_phase" not in st.session_state:
        st.session_state.story_phase = "beginning"

def query_groq(messages, max_tokens=400):
    body = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        logger.info("Making API request to Groq")
        response = requests.post(API_URL, headers=headers, json=body)
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}")
            return "The ancient tomes are temporarily sealed... Please try again."
        
        data = response.json()
        
        if "error" in data:
            logger.error(f"API returned error: {data['error']}")
            return "The mystical connection wavers... Please try again."
        
        if "choices" not in data or len(data["choices"]) == 0:
            logger.error("Unexpected API response structure")
            return "The story threads are tangled... Please try again."
        
        logger.info("API request successful")
        return data["choices"][0]["message"]["content"].strip()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return "The magical energies are unstable... Please try again."

def determine_story_phase(choice_count):
    if choice_count <= 3:
        return "beginning"
    elif choice_count <= 7:
        return "middle"
    elif choice_count <= 10:
        return "climax"
    else:
        return "ending"

def build_enhanced_system_prompt(original_setting, player_name, story_phase, choice_count):
    phase_guidance = {
        "beginning": "Focus on atmospheric world-building and mysterious character introduction.",
        "middle": "Develop the adventure with increasing mystique and intrigue.",
        "climax": "Build toward the peak with high stakes and magical tension.",
        "ending": f"Conclude the tale. If {choice_count} < 11, provide 3 choices that clearly guide toward closure. "
                  f"If {choice_count} >= 11, end the story fully with NO choices."
    }
    
    return f"""
You are an ancient storyteller, weaving tales of mystery and wonder in the tradition of dark academia.

STORY CONTEXT:
- Setting: "{original_setting}"
- Character: {player_name}
- Phase: {story_phase}
- Choices made: {choice_count}

GUIDANCE: {phase_guidance[story_phase]}

STYLE:
- Write in rich, atmospheric prose with scholarly undertones (90–130 words).
- Embrace themes of ancient knowledge, hidden secrets, and mystical discovery.
- Keep content appropriate for all audiences while maintaining sophistication.
- Maintain consistency with setting and previous events.

FORMAT (MANDATORY):
Always write in this exact format:

[Story text, 90–130 words]

CHOICES:
1. [Choice one – bold or scholarly]
2. [Choice two – cautious or investigative]
3. [Choice three – creative or intuitive]

IMPORTANT:
- If the story is ending (choice_count >= 11), do NOT output 'CHOICES:' at all. Only conclude the story.
- Otherwise ALWAYS provide exactly 3 distinct choices in the above format.
"""


def parse_enhanced_response(response):
    logger.info("Parsing response")
    
    if not response:
        return "", get_default_choices()
    
    # Method 1: Split by CHOICES: if present
    if "CHOICES:" in response:
        parts = response.split("CHOICES:", 1)  # Only split on first occurrence
        story_text = parts[0].strip()
        choices_text = parts[1].strip()
        choices = extract_choices(choices_text)
        return story_text, choices
    
    # Method 2: Find choices at the end
    lines = response.strip().split('\n')
    story_lines = []
    choice_lines = []
    
    # Look for where choices start (consecutive numbered/bulleted lines)
    choice_started = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line looks like a choice
        is_choice = bool(re.match(r'^\d+\.|\^[ABC]\.|\^[-•]', line))
        
        if is_choice and not choice_started:
            choice_started = True
            
        if choice_started:
            choice_lines.append(line)
        else:
            story_lines.append(line)
    
    story_text = '\n'.join(story_lines).strip()
    choices = extract_choices('\n'.join(choice_lines)) if choice_lines else []
    
    # Fallback if no story found
    if not story_text:
        story_text = response
    
    # Fallback if no choices found  
    if not choices:
        choices = get_default_choices()
    
    return story_text, choices[:3]

def extract_choices(text):
    """Extract clean choice text from formatted lines"""
    choices = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Remove common prefixes
        cleaned = re.sub(r'^\d+\.\s*|^[ABC]\.\s*|^[-•]\s*', '', line)
        if cleaned:
            choices.append(cleaned)
    
    return choices

def get_default_choices():
    return [
        "Consult ancient wisdom and proceed with scholarly confidence",
        "Exercise caution and gather more mystical knowledge", 
        "Trust intuition and embrace the unknown path"
    ]

def create_dark_academia_ui():
    st.set_page_config(
        page_title="Spiel",
        page_icon="📜",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    
    .main {
        background: #0a0a0a;
        color: #e8e6e3;
        font-family: 'Crimson Text', Georgia, serif;
    }
    
    .stApp {
        background: #0a0a0a;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        border: 1px solid #3d2b5c;
        border-radius: 8px;
        color: #e8e6e3;
        font-size: 16px;
        padding: 14px 18px;
        font-family: 'Crimson Text', Georgia, serif;
    }
    
    .stTextInput > div > div > input:focus {
        background-color: #1a1a1a;
        border: 1px solid #7c3aed;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
        outline: none;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #1a1a1a;
        border: 1px solid #3d2b5c;
        border-radius: 8px;
        color: #e8e6e3;
        font-size: 16px;
        padding: 14px 18px;
        font-family: 'Crimson Text', Georgia, serif;
    }
    
    .stTextArea > div > div > textarea:focus {
        background-color: #1a1a1a;
        border: 1px solid #7c3aed;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
        outline: none;
    }
    
    /* Story display */
    .story-segment {
        background: #1a1a1a;
        border: 1px solid #2d2d2d;
        border-radius: 12px;
        padding: 28px;
        margin: 24px 0;
        line-height: 1.8;
        font-size: 17px;
        color: #e8e6e3;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    }
    
    /* Choice styling */
    .choice-display {
        background: rgba(124, 58, 237, 0.1);
        border-radius: 8px;
        padding: 12px 18px;
        margin: 12px 0;
        font-size: 15px;
        color: #a78bfa;
        font-style: italic;
        border-left: 3px solid #7c3aed;
    }
    
    /* Button styling - enhanced for all buttons including form submit */
    .stButton > button {
        background: #1a1a1a;
        color: #e8e6e3;
        border: 1px solid #3d2b5c;
        border-radius: 8px;
        padding: 14px 24px;
        font-size: 15px;
        font-weight: 400;
        font-family: 'Crimson Text', Georgia, serif;
        width: 100%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .stButton > button:hover {
        background: #2d2d2d;
        border: 1px solid #7c3aed;
        color: #a78bfa;
    }
    
    /* Form submit button styling */
    .stFormSubmitButton > button {
        background: #7c3aed !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 14px 24px !important;
        font-family: 'Crimson Text', Georgia, serif !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4) !important;
    }
    
    .stFormSubmitButton > button:hover {
        background: #6d28d9 !important;
    }
    
    /* Hide streamlit elements */
    .stDeployButton, #MainMenu, header {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #e8e6e3;
        font-family: 'Crimson Text', Georgia, serif;
        font-weight: 600;
    }
    
    .subtitle {
        color: #a1a1aa;
        font-size: 24px;
        font-weight: 400;
        margin-bottom: 2.5rem;
        text-align: center;
        font-family: 'Crimson Text', Georgia, serif;
    }
    
    /* Title styling */
    .mystical-title {
        color: #a78bfa;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3d2b5c;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #7c3aed;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    initialize_session_state()
    create_dark_academia_ui()
    
    if not st.session_state.start:
        # Elegant mystical intro
        st.markdown("""
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h1 class='mystical-title' style='font-size: 3.5rem; margin-bottom: 0.5rem; letter-spacing: -0.02em;'>
                Spiel
            </h1>
            <div class='subtitle'>
                Weave your own tale of mystery and wonder... Who are you and what fate awaits? You tell us.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("mystical_intro", clear_on_submit=False):
            name = st.text_input(
                "Character Name",
                placeholder="Your name",
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            setting = st.text_area(
                "Adventure Setting", 
                placeholder="Describe the mystical realm where your tale unfolds...",
                height=90,
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col2:
                submitted = st.form_submit_button(
                    "Begin",
                    use_container_width=True
                )
            
            if submitted:
                if not name or not setting:
                    st.error("The ancient forces require both a name and setting to weave your tale...")
                elif not is_safe(name) or not is_safe(setting):
                    st.error("Please keep your chronicle appropriate for all who seek knowledge...")
                else:
                    with st.spinner("Consulting the ancient texts..."):
                        time.sleep(1.8)
                        
                    st.session_state.player_name = name
                    st.session_state.original_setting = setting
                    st.session_state.start = True
                    st.session_state.choice_count = 0
                    st.session_state.story_phase = "beginning"
                    
                    system_prompt = build_enhanced_system_prompt(
                        setting, name, "beginning", 0
                    )
                    
                    initial_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Begin the mystical chronicle for {name} in: {setting}"}
                    ]
                    
                    response = query_groq(initial_messages)
                    
                    if not any(phrase in response for phrase in ["ancient tomes", "mystical connection", "story threads"]) and is_safe(response):
                        story_text, choices = parse_enhanced_response(response)
                        st.session_state.history.append({
                            "story": story_text,
                            "choices": choices,
                            "timestamp": datetime.now()
                        })
                        st.success("Your chronicle begins! The threads of destiny are now woven...")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("The ancient texts are momentarily unclear. Please try again...")
                        st.session_state.start = False
    
    else:
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 35px; padding-bottom: 25px; 
                    border-bottom: 1px solid rgba(124, 58, 237, 0.2);'>
            <h2 style='color: #e8e6e3; font-weight: 400; margin: 0; font-size: 1.8rem;'>
                {st.session_state.player_name}
            </h2>
            <div style='color: #a78bfa; font-size: 14px; margin-top: 8px; font-style: italic;'>
                Chronicle {st.session_state.choice_count + 1}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for i, entry in enumerate(st.session_state.history):
            st.markdown(f"""
            <div class='story-segment'>
                {entry['story']}
            </div>
            """, unsafe_allow_html=True)
            
            if i > 0 and "chosen_option" in entry:
                st.markdown(f"""
                <div class='choice-display'>
                    {entry['chosen_option']}
                </div>
                """, unsafe_allow_html=True)
        
        # Current choices or ending
        if st.session_state.history:
            current_entry = st.session_state.history[-1]
            
            if st.session_state.choice_count >= 12:
                st.markdown("""
                <div style='text-align: center; margin: 50px 0; padding: 40px; 
                            background: #1a1a1a; border-radius: 15px;
                            border: 1px solid rgba(124, 58, 237, 0.3);'>
                    <h3 style='color: #a78bfa; margin-bottom: 20px; font-size: 1.6rem;'>
                        Chronicle Complete
                    </h3>
                    <div style='color: #a1a1aa; font-style: italic; font-size: 16px;'>
                        Your mystical tale has been inscribed in the eternal archives...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Balloons only at the very end like you wanted
                st.balloons()
                
                col1, col2, col3 = st.columns([1.5, 1, 1.5])
                with col2:
                    if st.button("New Chronicle", use_container_width=True, key="new_chronicle"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
                        
            else:
                choices = current_entry.get("choices", [])
                if choices:
                    st.markdown("""
                    <div style='text-align: center; margin: 25px 0; color: #a1a1aa; font-style: italic;'>
                    What path shall destiny weave?
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for j, choice in enumerate(choices):
                        if st.button(f"{choice}", key=f"choice_{len(st.session_state.history)}_{j}"):
                            st.session_state.choice_count += 1
                            st.session_state.story_phase = determine_story_phase(st.session_state.choice_count)
                            
                            with st.spinner("The mystical forces respond..."):
                                time.sleep(1.2)
                            
                            # Build conversation for context
                            conversation_history = [
                                {"role": "system", "content": build_enhanced_system_prompt(
                                    st.session_state.original_setting,
                                    st.session_state.player_name,
                                    st.session_state.story_phase,
                                    st.session_state.choice_count
                                )}
                            ]
                            
                            # Add recent context
                            for entry in st.session_state.history[-3:]:
                                conversation_history.append({
                                    "role": "assistant",
                                    "content": f"Story: {entry['story']}\nChoices: {', '.join(entry.get('choices', []))}"
                                })
                                if "chosen_option" in entry:
                                    conversation_history.append({
                                        "role": "user",
                                        "content": f"Chose: {entry['chosen_option']}"
                                    })
                            
                            conversation_history.append({
                                "role": "user",
                                "content": f"Chose: {choice}"
                            })
                            
                            response = query_groq(conversation_history)
                            
                            if not any(phrase in response for phrase in ["ancient tomes", "mystical connection", "story threads"]) and is_safe(response):
                                story_text, new_choices = parse_enhanced_response(response)
                                
                                st.session_state.history.append({
                                    "story": story_text,
                                    "choices": new_choices,
                                    "chosen_option": choice,
                                    "timestamp": datetime.now()
                                })
                                
                                st.rerun()
                            else:
                                st.error("The mystical energies waver... Please try again.")
        
        # Subtle restart option
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2.5, 1, 2.5])
        with col2:
            if st.button("Restart", use_container_width=True, key="restart_chronicle"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()