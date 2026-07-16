import random
from pyrogram import filters
from ShrutiMusic import app

TRUTHS = [
    "What is your most embarrassing moment?",
    "Who was your first crush?",
    "Have you ever lied to your best friend?",
    "What is your biggest secret?",
    "What's the weirdest dream you've ever had?",
    "Have you ever stalked someone on social media?",
    "What is the most childish thing you still do?",
    "Who in this group would survive a zombie apocalypse?",
    "What is your biggest fear?",
    "Have you ever sent a message to the wrong person?"
]

DARES = [
    "Send only emojis for the next 5 minutes.",
    "Change your profile photo for 10 minutes.",
    "Type 'I love potatoes' in the group.",
    "Do 10 squats.",
    "Sing your favorite song and send a voice note.",
    "Use only uppercase letters for 5 messages.",
    "Compliment 3 people in the group.",
    "Tell a funny joke right now.",
    "Send your last screenshot (if comfortable).",
    "Act like a cat for 1 minute."
]

@app.on_message(filters.command("truth"))
def get_truth(client, message):
    question = random.choice(TRUTHS)
    message.reply_text(
        f"🎲 **TRUTH QUESTION**\n\n{question}"
    )

@app.on_message(filters.command("dare"))
def get_dare(client, message):
    question = random.choice(DARES)
    message.reply_text(
        f"🔥 **DARE CHALLENGE**\n\n{question}"
    )

__MODULE__ = "Truth Or Dare"

__HELP__ = """
🎲 Truth Or Dare

/truth - Get a random truth question
/dare - Get a random dare challenge
"""