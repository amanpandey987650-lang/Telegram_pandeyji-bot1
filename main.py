import os
import threading
from flask import Flask
import telebot
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Ensure tokens are provided
if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN in environment variables.")

# 2. Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# 3. Initialize OpenAI Client (Pointed to Hugging Face Router)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_text = message.text
    
    # Show "typing..." status in Telegram while waiting for AI response
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Request completion from the Hugging Face router
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": user_text
                }
            ],
        )
        
        # Extract the AI's response and send it back to the user
        bot_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, bot_reply)
        
    except Exception as e:
        # Handle API errors gracefully
        bot.reply_to(message, f"Sorry, I encountered an error: {str(e)}")


# 5. Initialize Flask App (Required for Render hosting)
app = Flask(__name__)

@app.route('/')
def home():
    # This acts as a health check for Render. 
    # You can also use this URL in UptimeRobot to keep your free Render instance awake.
    return "Telegram AI Bot is running!"

# 6. Function to run the bot polling loop
def run_bot():
    print("Starting Telegram Bot...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Start the Telegram bot in a separate background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Start the Flask web server on the main thread
    # Render dynamically assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
