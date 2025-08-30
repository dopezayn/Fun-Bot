import os  
import asyncio  
import logging  
import re  
import requests  
import signal  
import sqlite3
import random
from datetime import datetime
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

# Multiple API keys support
openrouter_api_keys = [
    os.getenv("OPENROUTER_API_KEY_1"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
    os.getenv("OPENROUTER_API_KEY_4"),
    os.getenv("OPENROUTER_API_KEY_5"),
]
# Filter out None values
openrouter_api_keys = [key for key in openrouter_api_keys if key]

model_name = os.getenv("MODEL_NAME", "deepseek/deepseek-chat-v3-0324:free")  

# Fixed group and bot usernames  
group_username = "FUNToken_OfficialChat"  
bot_username = "fun_message_scoring_bot"  

# ------------------- API KEY MANAGEMENT -------------------
current_api_key_index = 0
api_key_status = {key: "active" for key in openrouter_api_keys}  # active, rate_limited, error

def get_next_api_key():
    """Get the next available API key with round-robin rotation"""
    global current_api_key_index
    
    if not openrouter_api_keys:
        log_with_time("No API keys available!", "❌", Fore.RED)
        return None
    
    # Try to find an active key
    for _ in range(len(openrouter_api_keys)):
        current_api_key_index = (current_api_key_index + 1) % len(openrouter_api_keys)
        key = openrouter_api_keys[current_api_key_index]
        if api_key_status.get(key) == "active":
            return key
    
    # If no active keys found, reset all to active and try again
    log_with_time("All API keys rate limited, resetting...", "🔄", Fore.YELLOW)
    for key in openrouter_api_keys:
        api_key_status[key] = "active"
    
    current_api_key_index = (current_api_key_index + 1) % len(openrouter_api_keys)
    return openrouter_api_keys[current_api_key_index]

def mark_api_key_status(key, status):
    """Mark an API key with specific status"""
    if key in api_key_status:
        api_key_status[key] = status
        log_with_time(f"API key status updated: {status}", "🔑", Fore.YELLOW)

# ------------------- SESSION -------------------  
SESSION_FOLDER = 'sessions'  
os.makedirs(SESSION_FOLDER, exist_ok=True)  
session_name = os.path.join(SESSION_FOLDER, "fun_quiz_session")  

# ------------------- LOGGING -------------------  
def log(msg, icon=">>>"):  
    print(Fore.CYAN + f"{icon} {msg}" + Style.RESET_ALL)  

def log_with_time(message, icon="ℹ️", color=Fore.WHITE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{timestamp}] {icon} {message}{Style.RESET_ALL}")

# ------------------- TEXT NORMALIZERS -------------------
def clean_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[\s\-_:;.,!()`\"'”“’•·\[\]{}<>]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_letter_token(s: str) -> str | None:
    s_low = s.lower()
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
    m = re.search(r"\b(?:option|ans(?:wer)?:?|choose|select)?\s*[\(\[]?\s*([a-e])\s*[\)\].:]?", s_low)
    if m:
        return m.group(1).upper()
    m2 = re.match(r"^\s*([a-e])\s*[\)\].:]", s_low)
    if m2:
        return m2.group(1).upper()
    return None

def strip_option_prefix(option_text: str) -> tuple[str, str]:
    raw = option_text.strip()
    emoji_to_letter = {"🅐": "A", "🅑": "B", "🅒": "C", "🅓": "D", "🅔": "E"}
    if len(raw) > 0 and raw[0] in emoji_to_letter:
        return emoji_to_letter[raw[0]], raw[1:].strip()
    m = re.match(r"^\s*[\(\[]?\s*([A-Ea-e])\s*[\)\].:]\s*(.+)$", raw)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return "", raw

def choose_button_from_ai(ai_answer: str, buttons) -> str | None:
    if not ai_answer:
        return None
    flat_btns = [btn for row in buttons for btn in row]
    options = [btn.text.strip() for btn in flat_btns]
    letter = extract_letter_token(ai_answer)
    if letter:
        idx = ord(letter) - ord('A')
        if 0 <= idx < len(options):
            return options[idx]
    ai_clean = clean_text(ai_answer)
    cleaned_options = []
    for opt in options:
        prefix_letter, body = strip_option_prefix(opt)
        cleaned_options.append((opt, clean_text(body)))
    for original_opt, cleaned_body in cleaned_options:
        if cleaned_body and (cleaned_body in ai_clean or ai_clean in cleaned_body):
            return original_opt
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

# ------------------- AI FUNCTION WITH MULTI-API SUPPORT -------------------  
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

    for attempt in range(1, 6):  # Increased to 5 attempts for multiple API keys
        api_key = get_next_api_key()
        if not api_key:
            log_with_time("No valid API keys available!", "❌", Fore.RED)
            return ""

        headers = {  
            "Authorization": f"Bearer {api_key}",  
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
            log_with_time(f"Attempt {attempt}: Using API key {openrouter_api_keys.index(api_key) + 1}", "📡", Fore.CYAN)
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data, timeout=25)  
            
            if response.status_code == 429:
                log_with_time(f"API key {openrouter_api_keys.index(api_key) + 1} rate limited!", "⏸️", Fore.YELLOW)
                mark_api_key_status(api_key, "rate_limited")
                continue
                
            elif response.status_code == 401:
                log_with_time(f"API key {openrouter_api_keys.index(api_key) + 1} invalid!", "❌", Fore.RED)
                mark_api_key_status(api_key, "error")
                continue
                
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"].strip()
                log_with_time(f"Success! Used API key {openrouter_api_keys.index(api_key) + 1}", "✅", Fore.GREEN)
                return answer  
            else:
                log_with_time(f"AI returned invalid response: {data}", "❌", Fore.RED)
                continue
                
        except requests.exceptions.RequestException as e:  
            log_with_time(f"Network error with API key {openrouter_api_keys.index(api_key) + 1}: {e}", "⚠️", Fore.RED)
            mark_api_key_status(api_key, "error")
        except Exception as e:  
            log_with_time(f"AI error with API key {openrouter_api_keys.index(api_key) + 1}: {e}", "❌", Fore.RED)
            mark_api_key_status(api_key, "error")

    log_with_time("Failed to get AI response after all attempts.", "❌", Fore.RED)
    return ""

# ------------------- BOT LOGIC -------------------
# Use StringSession instead of file-based session to avoid database lock issues
session_string = None
session_file = f"{session_name}.session"
if os.path.exists(session_file):
    try:
        with open(session_file, 'r') as f:
            session_string = f.read().strip()
    except:
        pass

if session_string:
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
else:
    client = TelegramClient(session_name, api_id, api_hash)

async def safe_start_client(max_retries=5):
    for attempt in range(max_retries):
        try:
            await client.start()
            # Save session as string for future use
            if not session_string:
                session_str = client.session.save()
                with open(session_file, 'w') as f:
                    f.write(session_str)
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                log_with_time(f"Database locked, waiting {wait_time} seconds...", "⚠️", Fore.YELLOW)
                await asyncio.sleep(wait_time)
            else:
                raise
    return False

async def run_bot():  
    if not await safe_start_client():
        log_with_time("Failed to start client after multiple attempts", "❌", Fore.RED)
        return
        
    log("Connected successfully", "🔌")  
    log_with_time(f"Loaded {len(openrouter_api_keys)} API keys", "🔑", Fore.GREEN)

    @client.on(events.NewMessage(chats=group_username))  
    async def handler(event):  
        message = event.message.message  

        if ("Quick Quiz!" in message or "Emoji Puzzle!" in message) and "Reward: 1 Wheel of Fortune spin" in message:  
            log("Quiz detected!", "✔️")  

            buttons = await event.get_buttons()  
            if not buttons:  
                log("No buttons found", "⚠️")  
                return  

            lines = message.split("\n")  
            question = ""  
            for line in lines:  
                if "?" in line:  
                    question = line.strip()  
                    break  

            if not question:  
                log("Question not found", "❌")  
                return  

            options = [btn.text.strip() for row in buttons for btn in row]  
            if not options:  
                log("Options not found", "❌")  
                return  

            log(f"Question: {question}", "🧠")  
            log("Sending to AI...", "📡")  

            ai_raw = get_ai_answer(question, options).strip()
            log(f"AI Answer: {ai_raw}", "🤖")  

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
        # Save session as string
        session_str = temp_client.session.save()
        with open(f"{session_name}.session", 'w') as f:
            f.write(session_str)
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