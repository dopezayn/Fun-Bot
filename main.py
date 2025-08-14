import os
import re
import requests
import signal
from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
from colorama import Fore, Style
from dotenv import load_dotenv

# ------------------- CLEAR CONSOLE -------------------
os.system('cls' if os.name == 'nt' else 'clear')

# ------------------- GRADIENT FUNCTION -------------------
def print_gradient(text):
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA]
    for i, char in enumerate(text):
        print(colors[i % len(colors)] + char, end='')
    print(Style.RESET_ALL)

# ------------------- ASCII ART -------------------
ascii_art = r"""
 __  __           _       _         
|  \/  | __ _  __| | __ _| |_ _   _ 
| |\/| |/ _` |/ _` |/ _` | __| | | |
| |  | | (_| | (_| | (_| | |_| |_| |
|_|  |_|\__,_|\__,_|\__,_|\__|\__, |
                              |___/ 
         Made by A K H I I
"""
print_gradient(ascii_art)

# ------------------- LOAD ENV -------------------
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ------------------- TELEGRAM CLIENT -------------------
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# ------------------- EXIT HANDLER -------------------
def handler(sig, frame):
    print("\n⚠️ Exiting...")
    client.disconnect()
    exit(0)

signal.signal(signal.SIGINT, handler)

# ------------------- AI REQUEST -------------------
def ask_ai(question, options):
    try:
        prompt = f"Question: {question}\nOptions: {', '.join(options)}\nGive only the correct option letter (A/B/C/D) or exact text."
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        data = r.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return extract_correct_option(answer, options)
    except Exception as e:
        print(f"❌ AI error: {e}")
        return None

# ------------------- OPTION EXTRACTION -------------------
def extract_correct_option(ai_answer, options):
    ai_answer_clean = ai_answer.lower().strip()

    # Check if AI gave only letter
    match = re.match(r"^\(?([a-d])\)?", ai_answer_clean)
    if match:
        letter = match.group(1).upper()
        index = ord(letter) - ord('A')
        if 0 <= index < len(options):
            return options[index]

    # Match by text
    for opt in options:
        if opt.lower() in ai_answer_clean:
            return opt

    return None

# ------------------- QUIZ DETECTOR -------------------
@client.on(events.NewMessage(chats="FUNToken_OfficialChat"))
async def handler_quiz(event):
    text = event.raw_text
    if "Quick Quiz!" in text and "Choose the correct option" in text:
        print("\n✔️ Quiz detected!")
        question_match = re.search(r"([^.?!]+[?])", text)
        question = question_match.group(1).strip() if question_match else "Unknown question"

        buttons = await event.get_buttons()
        options = [btn[0].text for btn in buttons]

        print(f"🧠 Question: {question}")
        print(f"📡 Sending to AI...")

        ai_option = ask_ai(question, options)
        if ai_option:
            for row in buttons:
                for btn in row:
                    if btn.text.strip().lower() == ai_option.strip().lower():
                        print(f"✅ Clicking answer: {btn.text}")
                        await btn.click()
                        return
            print("⚠️ Correct option not found in buttons.")
        else:
            print("⚠️ AI did not return a valid option.")

# ------------------- START BOT -------------------
print(">>> Listening for quizzes...")
client.start()
client.run_until_disconnected()