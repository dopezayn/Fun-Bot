import os
import asyncio
import logging
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
        prompt += f"{option_map[i]}) {opt}\n"

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert quiz solver."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
        answer = response.json()["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        log(f"AI error: {e}", "❌")
        return ""

# ------------------- BOT LOGIC -------------------
client = TelegramClient(session_name, api_id, api_hash)

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

            answer = get_ai_answer(question, options).lower()
            log(f"AI Answer: {answer}", "🤖")

            # Match AI answer with options
            selected = None
            for btn in [btn for row in buttons for btn in row]:
                if btn.text.lower() in answer or answer in btn.text.lower():
                    selected = btn
                    break

            if selected:
                log(f"Clicking answer: {selected.text}", "✅")
                await event.click(text=selected.text)
            else:
                log("Correct answer not found in options", "❌")

    log("Listening for quizzes...", ">>>")
    await client.run_until_disconnected()

# ------------------- SESSION CREATOR -------------------
async def create_session():
    print(Fore.YELLOW + "📱 Login to your Telegram account" + Style.RESET_ALL)
    async with TelegramClient(session_name, api_id, api_hash) as client:
        await client.start()
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