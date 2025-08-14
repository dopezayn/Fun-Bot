import os  
import asyncio  
import logging  
import re  
import requests  
import signal  
from telethon.sync import TelegramClient, events  
from telethon.sessions import StringSession  
from colorama import Fore, Style, init  
from dotenv import load_dotenv  

# ------------------- CLEAR CONSOLE -------------------  
os.system('cls' if os.name == 'nt' else 'clear')

# Colorama init
init(autoreset=True)

# ------------------- GRADIENT FUNCTION -------------------  
def print_gradient(text):  
    colors = [Fore.RED, Fore.MAGENTA, Fore.CYAN, Fore.BLUE]  
    for i, char in enumerate(text):  
        color = colors[i % len(colors)]  
        print(color + char, end="")  
    print(Style.RESET_ALL)  

# ------------------- ASCII ART WITH GRADIENT -------------------  
ascii_art = r"""  
███████╗██╗   ██╗███╗   ██╗     ██████╗ ██╗   ██╗██╗███████╗  
██╔════╝██║   ██║████╗  ██║    ██╔═══██╗██║   ██║██║██╔════╝  
███████╗██║   ██║██╔██╗ ██║    ██║   ██║██║   ██║██║█████╗    
╚════██║██║   ██║██║╚██╗██║    ██║   ██║██║   ██║██║██╔══╝    
███████║╚██████╔╝██║ ╚████║    ╚██████╔╝╚██████╔╝██║███████╗  
╚══════╝ ╚═════╝ ╚═╝  ╚═══╝     ╚═════╝  ╚═════╝ ╚═╝╚══════╝  
"""  
print_gradient(ascii_art)  
print_gradient("                 Made by A K H I I\n")  

# ------------------- LOAD ENV -------------------  
load_dotenv()  

api_id = int(os.getenv("API_ID"))  
api_hash = os.getenv("API_HASH")  
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")  
model_name = os.getenv("MODEL_NAME", "deepseek/deepseek-chat-v3-0324:free")  

# Fixed group and bot usernames  
group_username = "FUNToken_OfficialChat"  
bot_username = "fun_message_scoring_bot"  

# ------------------- SESSION -------------------  
SESSION_FOLDER = 'sessions'  
os.makedirs(SESSION_FOLDER, exist_ok=True)  
session_name = os.path.join(SESSION_FOLDER, "fun_quiz_session")  

# ------------------- LOGGING -------------------  
def log(msg, icon=">>>"):  
    print(Fore.CYAN + f"{icon} {msg}" + Style.RESET_ALL)  

# ------------------- TEXT NORMALIZERS -------------------
def clean_text(s: str) -> str:
    # Lowercase, strip spaces, remove punctuation-like chars for robust matching
    s = s.lower().strip()
    s = re.sub(r"[\s\-_:;.,!()`\"'”“’•·\[\]{}<>]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_letter_token(s: str) -> str | None:
    """
    Try to extract option letter A-E from strings like:
    'A', '(a)', 'option A', 'the answer is: e) virtual reality', '🅐', 'A.', 'A)'
    """
    s_low = s.lower()

    # Map fancy emoji letters to A-E
    emoji_map = {
        "🅐": "a", "🄐": "a",
        "🅑": "b", "🄑": "b",
        "🅒": "c", "🄒": "c",
        "🅓": "d", "🄓": "d",
        "🅔": "e", "🄔": "e",
    }
    for em, letter in emoji_map.items():
        if em in s:
            return letter.upper()

    # Common patterns: e.g. "answer: e", "(c)", "option d", "choose B", "A.", "B)"
    m = re.search(r"\b(?:option|ans(?:wer)?:?|choose|select)?\s*[\(\[]?\s*([a-e])\s*[\)\].:]?", s_low)
    if m:
        return m.group(1).upper()

    # Also check if line starts with letter format like "a) text" or "a . text"
    m2 = re.match(r"^\s*([a-e])\s*[\)\].:]", s_low)
    if m2:
        return m2.group(1).upper()

    return None

def strip_option_prefix(option_text: str) -> tuple[str, str]:
    """
    Return (letter_if_any, cleaned_option_text_without_letter_prefix)
    Detects prefixes like 'A) ', 'A. ', '🅐  ', etc.
    """
    raw = option_text.strip()
    # Emoji letters → letter
    emoji_to_letter = {"🅐": "A", "🅑": "B", "🅒": "C", "🅓": "D", "🅔": "E"}
    if len(raw) > 0 and raw[0] in emoji_to_letter:
        return emoji_to_letter[raw[0]], raw[1:].strip()

    # Alphabetic letters like "A) ..." / "A. ..." / "(A) ..."
    m = re.match(r"^\s*[\(\[]?\s*([A-Ea-e])\s*[\)\].:]\s*(.+)$", raw)
    if m:
        return m.group(1).upper(), m.group(2).strip()

    return "", raw

# ------------------- AI FUNCTION -------------------  
def get_ai_answer(question, options):  
    prompt = f"""  
You are a quiz solving AI. You will be given a question and options.  
Only reply with the exact correct option letter (A, B, C, D, E) or the exact option text.  

Question:  
{question}  

Options:  
"""  
    option_map = ["A", "B", "C", "D", "E"]  
    for i, opt in enumerate(options):  
        tag = option_map[i] if i < len(option_map) else f"Opt{i+1}"
        prompt += f"{tag}) {opt}\n"  

    headers = {  
        "Authorization": f"Bearer {openrouter_api_key}",  
        "Content-Type": "application/json"  
    }  
    json_data = {  
        "model": model_name,  
        "messages": [  
            {"role": "system", "content": "You are an expert quiz solver. Keep answers minimal."},  
            {"role": "user", "content": prompt}  
        ]  
    }  

    try:  
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data, timeout=25)  
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return answer  
    except Exception as e:  
        log(f"AI error: {e}", "❌")  
        return ""  

# ------------------- BOT LOGIC -------------------
client = TelegramClient(session_name, api_id, api_hash)  

def choose_button_from_ai(ai_answer: str, buttons) -> str | None:
    """
    Returns the exact button text to click, or None
    """
    if not ai_answer:
        return None

    # Prepare options (flatten buttons)
    flat_btns = [btn for row in buttons for btn in row]
    options = [btn.text.strip() for btn in flat_btns]

    # 1) If AI provided a letter → map to index
    letter = extract_letter_token(ai_answer)
    if letter:
        idx = ord(letter) - ord('A')
        if 0 <= idx < len(options):
            return options[idx]

    # 2) Try to match option text (robust cleaning)
    ai_clean = clean_text(ai_answer)
    cleaned_options = []
    for opt in options:
        prefix_letter, body = strip_option_prefix(opt)
        cleaned_options.append((opt, clean_text(body)))

    # Exact contains or equality match (clean)
    for original_opt, cleaned_body in cleaned_options:
        if cleaned_body and (cleaned_body in ai_clean or ai_clean in cleaned_body):
            return original_opt

    # Last resort: loose token overlap
    ai_tokens = set(ai_clean.split())
    best_score, best_opt = 0, None
    for original_opt, cleaned_body in cleaned_options:
        opt_tokens = set(cleaned_body.split())
        score = len(ai_tokens & opt_tokens)
        if score > best_score and score > 0:
            best_score, best_opt = score, original_opt
    if best_opt:
        return best_opt

    return None

async def run_bot():  
    await client.start()  
    log("Connected successfully", "🔌")  

    @client.on(events.NewMessage(chats=group_username))  
    async def handler(event):  
        message = event.message.message  

        if ("Quick Quiz!" in message or "Emoji Puzzle!" in message) and "Reward: 1 Wheel of Fortune spin" in message:  
            log("Quiz detected!", "✔️")  

            buttons = await event.get_buttons()  
            if not buttons:  
                log("No buttons found", "⚠️")  
                return  

            # Extract question  
            lines = message.split("\n")  
            question = ""  
            for line in lines:  
                if "?" in line:  
                    question = line.strip()  
                    break  

            if not question:  
                log("Question not found", "❌")  
                return  

            # Extract options  
            options = [btn.text.strip() for row in buttons for btn in row]  
            if not options:  
                log("Options not found", "❌")  
                return  

            log(f"Question: {question}", "🧠")  
            log("Sending to AI...", "📡")  

            ai_raw = get_ai_answer(question, options).strip()
            log(f"AI Answer: {ai_raw}", "🤖")  

            # Decide which button to click
            target_text = choose_button_from_ai(ai_raw, buttons)

            if target_text:
                log(f"Clicking answer: {target_text}", "✅")
                await event.click(text=target_text)
            else:
                log("Correct answer not found in options", "❌")  

    log("Listening for quizzes...", ">>>")  
    await client.run_until_disconnected()  

# ------------------- SESSION CREATOR -------------------  
async def create_session():  
    print(Fore.YELLOW + "📱 Login to your Telegram account" + Style.RESET_ALL)  
    async with TelegramClient(session_name, api_id, api_hash) as temp_client:  
        await temp_client.start()  
        print(Fore.GREEN + "✅ Session created and saved!" + Style.RESET_ALL)  

# ------------------- GRACEFUL SHUTDOWN -------------------  
def shutdown(loop):  
    print("\nGracefully shutting down...")  
    loop.create_task(client.disconnect())  

# ------------------- MENU -------------------  
if __name__ == "__main__":  
    loop = asyncio.get_event_loop()  
    for sig in (signal.SIGINT, signal.SIGTERM):  
        loop.add_signal_handler(sig, lambda: shutdown(loop))  

    print(Fore.MAGENTA + "\n=== FUN QUIZ BOT MENU ===" + Style.RESET_ALL)  
    print("1️⃣ Create Session (Login with Telegram)")  
    print("2️⃣ Run Bot")  
    choice = input(Fore.CYAN + "\nSelect an option (1 or 2): " + Style.RESET_ALL)  

    if choice == "1":  
        asyncio.run(create_session())  
    elif choice == "2":  
        try:  
            asyncio.run(run_bot())  
        except KeyboardInterrupt:  
            print("Bot stopped by user.")  
            loop.run_until_complete(client.disconnect())  
            loop.close()  
    else:  
        print(Fore.RED + "❌ Invalid choice. Please select 1 or 2." + Style.RESET_ALL)