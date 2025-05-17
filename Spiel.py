import streamlit as st
import requests
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://api.mistral.ai/v1/chat/completions"
API_KEY = st.secrets["API_KEY"] 
MODEL_NAME = "open-mistral-7b"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

banned_words = [
    "whore", "fuck", "shit", "bitch", "cunt", "dick", "cock", "pussy", "penis", "vagina",
    "asshole", "rape", "molest", "porn", "prostitute", "whorehouse", "orgy", "slut",
    "masturbate", "fetish", "erotic", "xxx", "nude", "nudity", "incest", "bestiality"
]

def is_safe(text):
    clean_text = re.sub(r'[^a-zA-Z]', '', text.lower())
    for word in banned_words:
        if word in clean_text:
            return False
    return True

if "history" not in st.session_state:
    st.session_state.history = []
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "start" not in st.session_state:
    st.session_state.start = False

def query_mistral(prompt):
    body = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 300,
        "stream": False
    }
    try:
        logger.info("Making API request to Mistral")
        response = requests.post(API_URL, headers=headers, json=body)
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}")
            return "Trouble in fairyland, come back later!"
        data = response.json()
        if "error" in data:
            logger.error(f"API returned error: {data['error']}")
            return "Trouble in fairyland, come back later!"
        if "choices" not in data or len(data["choices"]) == 0:
            logger.error("Unexpected API response structure")
            return "Trouble in fairyland, come back later!"
        logger.info("API request successful")
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return "Trouble in fairyland, come back later!"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "Trouble in fairyland, come back later!"

def parse_response(response):
    logger.info("Parsing AI response")
    response = response.replace("[STORY TEXT HERE]", "").strip()
    if "CHOICES:" in response:
        parts = response.split("CHOICES:")
        story_text = parts[0].strip()
        choices_text = parts[1].strip()
        choices = []
        for line in choices_text.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                choice = line.split('.', 1)[1].strip()
                if choice:
                    choices.append(choice)
        logger.info(f"Parsed {len(choices)} choices from response")
        return story_text, choices
    else:
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        story_lines = []
        choices = []
        potential_choices = []
        story_content = []
        for i, line in enumerate(lines):
            if any(line.startswith(prefix) for prefix in ["-", "•", "1.", "2.", "3.", "A.", "B.", "C."]):
                potential_choices.append(line)
            elif line.endswith(('.', '!', '?', '"')) and i < len(lines) - 1:
                story_content.append(line)
                remaining_lines = lines[i+1:]
                if all(any(l.startswith(prefix) for prefix in ["-", "•", "1.", "2.", "3.", "A.", "B.", "C."]) for l in remaining_lines if l):
                    potential_choices.extend(remaining_lines)
                    break
            else:
                story_content.append(line)
        if potential_choices:
            for choice_line in potential_choices:
                for prefix in ["-", "•", "1.", "2.", "3.", "A.", "B.", "C."]:
                    if choice_line.startswith(prefix):
                        choice = choice_line[len(prefix):].strip()
                        if choice:
                            choices.append(choice)
                        break
        if choices:
            story_text = '\n'.join(story_content).strip()
        else:
            story_text = '\n'.join(lines).strip()
            choices = ["Open the envelope", "Ignore it and continue", "Look around for the source of the whisper"]
        logger.info(f"Fallback parsing: {len(choices)} choices extracted")
        return story_text, choices

def build_initial_prompt(setting, name):
    logger.info(f"Building initial prompt for {name} in setting: {setting[:50]}...")
    return f"""You are Story Master, the narrator of an immersive text adventure game.
Start a compelling story based on the following setting: "{setting}", involving the player character named {name}.
Write an engaging story paragraph that sets the scene and presents a situation. Then provide exactly 3 choices.
End your response with:
CHOICES:
1. [First choice]
2. [Second choice] 
3. [Third choice]
Do not include any placeholder text like [STORY TEXT HERE]. Write the actual story content directly.
Keep your response under 150 words total. No adult or offensive content. Keep it PG-13.
"""

def build_choice_prompt(choice):
    logger.info(f"Building choice prompt for: {choice}")
    return f"""Continue the interactive text adventure game. The player chose: "{choice}".
Write what happens next in the story, then provide exactly 3 new choices for what to do next.
End your response with:
CHOICES:
1. [First choice]
2. [Second choice]
3. [Third choice]
Do not include any placeholder text. Keep it PG-13. No adult or offensive content.
If the adventure has reached 12 or more player choices, narrate a satisfying ending instead of offering choices.
Keep your response under 100 words total.
"""

st.set_page_config(page_title="Spiel", layout="centered")

st.markdown("""<h1 style='color: #D94B4B; font-size: 6rem; font-weight: bold;'>Spiel</h1>""", unsafe_allow_html=True)

if not st.session_state.start:
    with st.form("intro"):
        name = st.text_input("What should the player be called?", "")
        setting = st.text_area("Describe the setting to begin your adventure", "")
        submitted = st.form_submit_button("Start the Adventure")
        if submitted:
            if not name or not setting:
                st.error("Name and setting required.")
            elif not is_safe(name) or not is_safe(setting):
                st.error("Please keep it appropriate and PG-13.")
            else:
                logger.info(f"Starting new adventure for {name}")
                st.session_state.player_name = name
                st.session_state.start = True
                initial_prompt = build_initial_prompt(setting, name)
                response = query_mistral(initial_prompt)
                if response == "Trouble in fairyland, come back later!":
                    st.error(response)
                    st.session_state.start = False
                elif not is_safe(response):
                    st.error("Story contained inappropriate content. Try a different setting.")
                    st.session_state.start = False
                else:
                    story_text, choices = parse_response(response)
                    st.session_state.history.append({"npc": story_text, "choices": choices})
                    st.rerun()
else:
    for i, entry in enumerate(st.session_state.history):
        st.markdown(f"**Story Master:** {entry['npc']}")
        if i > 0 and "choice" in entry:
            st.markdown(f"""<div style='background-color: #D94B4B; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #D94B4B;'>🎮 <strong>You chose:</strong> <em>{entry['choice']}</em></div>""", unsafe_allow_html=True)
    if st.session_state.history:
        if len(st.session_state.history) >= 13:
            st.markdown("The adventure has come to its conclusion. Restart to begin a new journey.")
        else:
            current_entry = st.session_state.history[-1]
            choices = current_entry.get("choices", ["Look around", "Continue forward", "Ask for help"])
            st.markdown("#### What will you do?")
            for choice in choices:
                if st.button(choice, key=f"choice_{len(st.session_state.history)}_{choice}"):
                    logger.info(f"Player chose: {choice}")
                    prompt = build_choice_prompt(choice)
                    response = query_mistral(prompt)
                    if response == "Trouble in fairyland, come back later!":
                        st.error(response)
                    elif not is_safe(response):
                        st.error("Story contained inappropriate content. Try a different choice.")
                    else:
                        story_text, new_choices = parse_response(response)
                        st.session_state.history.append({"choice": choice, "npc": story_text, "choices": new_choices})
                        st.rerun()
    if st.button("Restart"):
        logger.info("Restarting game")
        st.session_state.clear()
        st.rerun()