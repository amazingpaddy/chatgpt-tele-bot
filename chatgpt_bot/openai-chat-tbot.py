# Import the necessary modules

from telebot import types
import os
import requests
from telebot.async_telebot import AsyncTeleBot
from flask import Flask, request

API_KEY = os.environ.get('OPENAI_API_KEY')
MODEL = 'text-davinci-003'
BOT_TOKEN = os.environ.get('GPT_BOT_TOKEN')
BOT_PERSONALITY = 'Friendly'
authorized_users = [] # Add authorized usernames here without @ symbol

# Create an asynchronous bot object with the token
bot = AsyncTeleBot(BOT_TOKEN)

# Create a Flask app object with the current module name
app = Flask(__name__)

# Define a route for handling POST requests from Telegram
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def handle_update():
    # Get the JSON data from the request and convert it to an Update object
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    # Process the update with the bot object asynchronously
    await bot.process_new_updates([update])
    # Return a success response to Telegram
    return 'ok'


async def openAI(prompt):
    # Make the request to the OpenAI API
    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'model': MODEL, 'prompt': prompt, 'temperature': 0.4, 'max_tokens': 3000}
    )
    result = response.json()
    print(result)
    final_result = ''.join(choice['text'] for choice in result['choices'])
    return final_result


@bot.message_handler(commands=['ask'])
async def ask(message):
    try:
        username = message.from_user.username
        if username not in authorized_users:
            await bot.reply_to(message, "Not authorized to use this bot")
            return
        prompt = message.text.replace("/ask", "")
        print(f"Request received from {username} - {message.text} - {prompt}")
        if not prompt:
            await bot.reply_to(message, "Empty query sent. Add your query /ask <message>")
        else:
            bot_response = await openAI(f"{BOT_PERSONALITY}{prompt.strip()}")
            print(f"Response received - {bot_response}")
            await bot.reply_to(message, bot_response.replace('?\n\n', ''))
    except Exception as e:
        print("Exception happened")
        print(e)


@bot.message_handler(commands=['start'])
async def start(message):
    try:
        username = message.from_user.username
        result = f"""
        Welcome {username}!!, With this bot, you can send your queries to ChatGPT and receive responses. 
        To post your questions, use the "/ask <message>" format. 
        For example, type "/ask Explain like I'm 5, what is entropy?"
        Please allow 1-2 minutes for a reply. 
        If you don't receive a response, try again later. 
        Note that the bot does not retain previous conversations, so follow-up questions 
        may not receive the expected answer from ChatGPT.
        """
        await bot.send_message(message.chat.id, result)
    except Exception as e:
        print("Exception happened")
        print(e)


# Get the port number from an environment variable or use 5000 as default
PORT = int(os.environ.get('PORT', 5000))

# Run the app on a specified host and port in debug mode if this module is executed directly
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True)
