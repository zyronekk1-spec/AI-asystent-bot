import discord
from discord.ext import commands
import aiohttp
import os


# ================== KONFIGURACJA ==================

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CHANNEL_ID = None
MAX_HISTORY = 5


SYSTEM_PROMPT = """
Jesteś przyjaznym botem Discord.
Rozmawiasz naturalnie, krótko i pomocnie.
Odpowiadasz po polsku.
Zachowujesz się jak zwykły pomocny rozmówca.
"""


# ================== DISCORD ==================

intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


conversation_history = {}



@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="rozmów 💬"
        )
    )



@bot.event
async def on_message(message):

    if message.author.bot:
        return


    if bot.user not in message.mentions:
        return


    if CHANNEL_ID and message.channel.id != CHANNEL_ID:
        return



    user_content = (
        message.content
        .replace(f"<@{bot.user.id}>", "")
        .replace(f"<@!{bot.user.id}>", "")
        .strip()
    )


    if not user_content:
        await message.reply(
            "Napisz wiadomość 🙂"
        )
        return



    channel_id = message.channel.id


    if channel_id not in conversation_history:
        conversation_history[channel_id] = []


    history = conversation_history[channel_id]


    history.append({
        "role": "user",
        "content": user_content
    })


    if len(history) > MAX_HISTORY:
        conversation_history[channel_id] = history[-MAX_HISTORY:]
        history = conversation_history[channel_id]



    try:

        async with message.channel.typing():

            reply = await generate_response(history)


        history.append({
            "role": "assistant",
            "content": reply
        })


        if len(reply) > 2000:
            reply = reply[:1990] + "..."


        await message.reply(reply)



    except Exception as e:

        print("BŁĄD:", e)

        await message.reply(
            "Wystąpił błąd podczas generowania odpowiedzi."
        )



# ================== GROQ ==================


async def generate_response(history):


    if not GROQ_API_KEY:
        raise Exception(
            "Brak GROQ_API_KEY"
        )



    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + history



    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }



    payload = {

        "model": "llama-3.1-8b-instant",

        "messages": messages,

        "temperature": 0.8,

        "max_tokens": 500
    }



    async with aiohttp.ClientSession() as session:

        async with session.post(

            "https://api.groq.com/openai/v1/chat/completions",

            headers=headers,

            json=payload

        ) as response:



            data = await response.json()



            print("STATUS GROQ:", response.status)

            print("GROQ:", data)



            if response.status != 200:

                raise Exception(data)



            if "choices" not in data:

                raise Exception(
                    f"Brak choices: {data}"
                )



            return data["choices"][0]["message"]["content"].strip()




# ================== START ==================


if __name__ == "__main__":


    if not TOKEN:

        raise Exception(
            "Brak DISCORD_TOKEN"
        )


    if not GROQ_API_KEY:

        raise Exception(
            "Brak GROQ_API_KEY"
        )


    bot.run(TOKEN)
