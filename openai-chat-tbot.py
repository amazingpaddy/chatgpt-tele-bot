# Import the necessary modules

from telebot import types
import os
import requests
from telebot.async_telebot import AsyncTeleBot
from flask import Flask, request

# Get OpenAI API key, Telegram bot token, bot personality, and authorized users from environment variables
API_KEY = os.environ.get('OPENAI_API_KEY')
BOT_TOKEN = os.environ.get('GPT_BOT_TOKEN')
authorized_users = os.environ.get('AUTHORIZED_USERS').split(',')
BOT_PERSONALITY = os.environ.get('BOT_PERSONALITY').split(',')

# Set OpenAI model and bot personality
MODEL = 'text-davinci-003'

# Create an asynchronous bot object with the Telegram bot token
bot = AsyncTeleBot(BOT_TOKEN)

# Create a Flask app object with the current module name
app = Flask(__name__)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def handle_update():
    """
    Handle incoming POST requests from Telegram.

    Convert the JSON data in the request to an Update object,
    process it asynchronously using the bot object, and return a success response.
    """
    # Get the JSON data from the request and convert it to an Update object
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)

    # Process the update with the bot object asynchronously
    await bot.process_new_updates([update])

    # Return a success response to Telegram
    return 'ok'


async def openAI(prompt):
    """
    Make a request to the OpenAI API and return the response.

    Parameters:
    prompt (str): The prompt to send to the OpenAI API.

    Returns:
    str: The response from the OpenAI API.
    """
    # Make the request to the OpenAI API
    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'model': MODEL, 'prompt': prompt, 'temperature': 0.4, 'max_tokens': 3000}
    )

    # Parse the response and return the result
    result = response.json()
    final_result = ''.join(choice['text'] for choice in result['choices'])
    return final_result


@bot.message_handler(commands=['ask'])
async def ask(message):
    """
    Handle messages that start with the "/ask" command.

    Check if the user is authorized to use the bot, extract the query from the message,
    pass it to the openAI function for processing, and send the response back to the user.
    """
    try:
        # Get the username of the message sender
        username = message.from_user.username

        # Check if the user is authorized to use the bot
        if username not in authorized_users:
            await bot.reply_to(message, "Not authorized to use this bot")
            return

        # Extract the query from the message
        prompt = message.text.replace("/ask", "").strip()

        # If the query is empty, send an error message to the user
        if not prompt:
            await bot.reply_to(message, "Empty query sent. Add your query /ask <message>")
        else:
            # Send the query to the OpenAI API and get the response
            bot_response = await openAI(f"{BOT_PERSONALITY}{prompt}")

            # Send the response back to the user
            await bot.reply_to(message, bot_response.replace('?\n\n', ''))

    except Exception as e:
        print("Exception happened")
        print(e)


@bot.message_handler(commands=['start'])
async def start(message):
    """
    Handle '/start' command from user and send a welcome message with instructions on how to use the bot.

    Args:
        message (:obj:`telebot.types.Message`): The message object representing the '/start' command.

    Returns:
        None
    """
    try:
        # Get the username of the user who sent the '/start' command
        username = message.from_user.username
        # Create the welcome message
        result = f"""
        Welcome {username}!!, With this bot, you can send your queries to ChatGPT and receive responses. 
        To post your questions, use the "/ask <message>" format. 
        For example, type "/ask Explain like I'm 5, what is entropy?"
        Please allow 1-2 minutes for a reply. 
        If you don't receive a response, try again later. 
        Note that the bot does not retain previous conversations, so follow-up questions 
        may not receive the expected answer from ChatGPT.
        Thanks for using this bot - Paddy!!
        """
        # Send the welcome message to the user
        await bot.send_message(message.chat.id, result)
    except Exception as e:
        # If an exception occurs, print the error message to the console
        print("Exception happened")
        print(e)


# Get the port number from an environment variable or use 5000 as default
PORT = int(os.environ.get('PORT', 5000))

# Run the app on a specified host and port in debug mode if this module is executed directly
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True)
