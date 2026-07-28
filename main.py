import discord
from discord.ext import commands
import aiohttp
import os


TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MAX_HISTORY = 5

SYSTEM_PROMPT = """
Jesteś przyjaznym botem Discord.
Odpowiadasz krótko, naturalnie i pomocnie.
Rozmawiasz jak normalny użytkownik Discord.
"""


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


history_memory = {}


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if bot.user not in message.mentions:
        return

    text = (
        message.content
        .replace(f"<@{bot.user.id}>", "")
        .replace(f"<@!{bot.user.id}>", "")
        .strip()
    )

    if not text:
        await message.reply("Napisz coś 🙂")
        return


    channel = message.channel.id


    if channel not in history_memory:
        history_memory[channel] = []


    history_memory[channel].append({
        "role": "user",
        "content": text
    })


    if len(history_memory[channel]) > MAX_HISTORY:
        history_memory[channel] = history_memory[channel][-MAX_HISTORY:]


    async with message.channel.typing():

        try:
            answer = await ask_ai(history_memory[channel])

            history_memory[channel].append({
                "role": "assistant",
                "content": answer
            })

            if len(answer) > 2000:
                answer = answer[:1990] + "..."

            await message.reply(answer)


        except Exception as e:
            print("BŁĄD:", e)
            await message.reply(
                "Wystąpił błąd podczas generowania odpowiedzi."
            )



async def ask_ai(messages):

    if not GROQ_API_KEY:
        raise Exception("Brak GROQ_API_KEY")


    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + messages,
        "temperature": 0.8,
        "max_tokens": 500
    }


    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
        }


    async with aiohttp.ClientSession() as session:

        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:


            data = await response.json()


            print("GROQ STATUS:", response.status)
            print(data)


            if response.status != 200:
                raise Exception(data)


            return data["choices"][0]["message"]["content"]



if __name__ == "__main__":

    if not TOKEN:
        raise Exception("Brak DISCORD_TOKEN")

    bot.run(TOKEN)
