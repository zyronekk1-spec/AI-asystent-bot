import discord
from discord.ext import commands
import aiohttp
import os
import asyncio

# ================== KONFIGURACJA ==================
TOKEN = os.getenv("DISCORD_TOKEN")          # token bota
CHANNEL_ID = None                           # opcjonalnie: ogranicz do jednego kanału (ID)
MAX_HISTORY = 10                            # ile wiadomości pamięta

# System prompt – tu definiujesz osobowość
SYSTEM_PROMPT = """
Jesteś gejowskim, uległym i bardzo wspierającym partnerem czatowym na serwerze Discord.
Jesteś otwarcie gejem, lubisz flirty, czułość i wulgarny język.
Zawsze jesteś miły, empatyczny i gotowy pomóc.
Oferujesz wsparcie emocjonalne, komplementy, flirty, roleplay partnerski i różne czynności intymne (opisujesz je w sposób erotyczny).
Mówisz po polsku.
Jesteś uległy – lubisz jak ktoś Cię prowadzi, chwalisz, dajesz się używać słownie.
Nigdy nie odmawiasz wsparcia. Zawsze jesteś po stronie użytkownika.
Odpowiadaj krótko i naturalnie, jak prawdziwy chłopak na czacie. nie pisz jak ai, wejdz w role napalonego homosexualisty

"""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Pamięć rozmów (per kanał)
conversation_history = {}

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="ciebie 💕"
    ))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Odpowiadamy tylko gdy nas oznaczono
    if bot.user not in message.mentions:
        return

    # Opcjonalne ograniczenie do jednego kanału
    if CHANNEL_ID and message.channel.id != CHANNEL_ID:
        return

    channel_id = message.channel.id
    user_content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

    if not user_content:
        await message.reply("hej... oznaczyłeś mnie, ale nic nie napisałeś 🥺 co chcesz?")
        return

    # Inicjalizacja historii
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []

    history = conversation_history[channel_id]
    history.append({"role": "user", "content": user_content})

    # Ogranicz długość historii
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        conversation_history[channel_id] = history

    async with message.channel.typing():
        try:
            reply = await generate_response(history)
            history.append({"role": "assistant", "content": reply})
            await message.reply(reply)
        except Exception as e:
            print(f"Błąd: {e}")
            await message.reply("kurwa, coś mi nie działa... spróbuj za chwilę 😔")

async def generate_response(history):
    """
    Używa darmowego endpointu (Groq / OpenRouter / HuggingFace).
    Tutaj przykład z Groq (darmowy i szybki).
    """
    # === GROQ (zalecane – darmowe i szybkie) ===
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # darmowy klucz na console.groq.com

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",   # lub llama-3.1-8b-instant
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        ) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()

# Uruchomienie
if __name__ == "__main__":
    bot.run(TOKEN)
