# request.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import tmdbsimple as tmdb
import asyncio

tmdb.API_KEY = "2937f761448c84e103d3ea8699d5a33c"  # Your TMDB API Key
ADMIN_CHANNEL = -1002652331022  # Replace with your channel ID

# Only allow in groups
group_only = filters.group & filters.command("request")

@Client.on_message(group_only)
async def movie_request(client: Client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("🎬 Please type movie name after /request\n\nExample: `/request Inception`", quote=True)

    # Search on TMDB
    search = tmdb.Search()
    response = search.movie(query=query)
    results = response.get("results", [])[:4]

    if not results:
        return await message.reply("❌ No similar movie found. Please check spelling.", quote=True)

    # Show similar movie options
    buttons = [
        [InlineKeyboardButton(movie["title"], callback_data=f"confirm_request|{message.from_user.id}|{movie['title']}")]
        for movie in results
    ]

    await message.reply(
        f"🔍 Did you mean one of these movies?",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

@Client.on_callback_query(filters.regex(r"^confirm_request\|"))
async def confirm_request(client: Client, callback_query: CallbackQuery):
    _, user_id, movie_name = callback_query.data.split("|")
    user_id = int(user_id)

    # Confirm to user
    try:
        await client.send_message(user_id, f"✅ Your request for **{movie_name}** has been accepted and will be uploaded soon.")
    except:
        pass  # if user blocked bot etc.

    # Send to admin channel with buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Uploaded", callback_data=f"uploaded|{user_id}|{movie_name}")],
        [InlineKeyboardButton("❌ Unavailable", callback_data=f"unavailable|{user_id}|{movie_name}")],
        [InlineKeyboardButton("🟡 Already Uploaded", callback_data=f"already|{user_id}|{movie_name}")],
        [InlineKeyboardButton("✏️ Wrong Name", callback_data=f"wrong|{user_id}|{movie_name}")]
    ])

    await client.send_message(
        ADMIN_CHANNEL,
        f"🎬 New Movie Request:\n\n📽️ **{movie_name}**\n👤 From: [User](tg://user?id={user_id})",
        reply_markup=keyboard
    )

    await callback_query.answer("✅ Request confirmed.")

@Client.on_callback_query(filters.regex(r"^(uploaded|unavailable|already|wrong)\|"))
async def handle_admin_response(client: Client, callback_query: CallbackQuery):
    action, user_id, movie_name = callback_query.data.split("|")
    user_id = int(user_id)

    msg = {
        "uploaded": f"✅ Your movie **{movie_name}** has been uploaded!",
        "unavailable": f"❌ Sorry, **{movie_name}** is currently unavailable.",
        "already": f"ℹ️ **{movie_name}** is already uploaded.",
        "wrong": f"⚠️ The movie name **{movie_name}** seems wrong.\nPlease send the correct name."
    }

    try:
        await client.send_message(user_id, msg[action])
    except:
        pass

    await callback_query.answer("✅ Response sent.")
