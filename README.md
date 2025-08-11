README.md Example for Your Quiz Bot

# Fun Quiz Bot

This Telegram bot automatically detects quiz questions in the [FUNToken Official Chat](https://t.me/FUNToken_OfficialChat) and answers them using AI (OpenRouter GPT models).

---

## Features

- Listens to quiz messages in the specified Telegram group
- Sends questions to OpenRouter GPT AI for answers
- Automatically clicks the correct answer button
- Colorful and informative console logs

---

## Setup Instructions

Follow these steps carefully to set up and run the bot on your system.

---

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo


---

2. Create .env file

Copy the example environment file and fill in your own credentials:

cp .env.example .env

Open .env in any text editor and update the following variables with your own values:

Variable	Description

API_ID	Your Telegram API ID (integer)
API_HASH	Your Telegram API hash (string)
SESSION_NAME	Name for your Telethon session file (string)
GROUP_USERNAME	Telegram group username where quizzes appear
BOT_USERNAME	Telegram bot username used for scoring (if any)
OPENROUTER_API_KEY	Your OpenRouter API key to access GPT models
MODEL_NAME	AI model name (default: openai/gpt-3.5-turbo)



---

3. How to get your Telegram API ID and API Hash

1. Go to my.telegram.org


2. Log in with your Telegram phone number


3. Click on "API Development Tools"


4. Create a new application if you don't have one


5. Copy your api_id and api_hash from there and paste them into your .env file




---

4. How to get your OpenRouter API Key

1. Visit https://openrouter.ai


2. Sign up for a free account (or log in if you already have one)


3. Go to your dashboard or API keys section


4. Create a new API key


5. Copy the key and paste it into your .env file under OPENROUTER_API_KEY




---

5. Install dependencies

Make sure you have Python 3.8+ installed. Then install required packages:

pip install -r requirements.txt

If requirements.txt is not available, install manually:

pip install telethon requests colorama python-dotenv


---

6. Run the bot

python main.py

The bot will start and connect to Telegram. It will listen to quizzes and answer automatically.


---

7. Important Notes

Do NOT share your .env file publicly — it contains sensitive API keys.

If you want to reset your session, delete the .session file created with the name you provided in SESSION_NAME.

Keep your API keys secret and secure.

For any issues, raise an issue on the GitHub repo or contact the maintainer.



---

License

MIT License


---

Made with ❤️ by [Your Name or Username]
