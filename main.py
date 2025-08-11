import asyncio
import logging
import re
import requests
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient, events
from colorama import Fore, Style

# Load environment variables
load_dotenv()

# ------------------- CONFIG -------------------
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")
group_username = os.getenv("GROUP_USERNAME")
bot_username = os.getenv("BOT_USERNAME")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("MODEL_NAME")

# ------------------- LOGGING -------------------
def log(msg, icon=">>>"):
    print(Fore.CYAN + f"{icon} {msg}" + Style.RESET_ALL)

# ------------------- AI FUNCTION -------------------
def get_ai_answer(question, options):
    prompt = f"""
You are a quiz solving AI. You will be given a question and options.
Only reply with the exact correct option letter (A, B, C, D) or the exact option text.

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

# ------------------- MAIN BOT -------------------
async def main():
    client = TelegramClient(session_name, api_id, api_hash)
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

# ------------------- RUN -------------------
if __name__ == "__main__":
    asyncio.run(main())