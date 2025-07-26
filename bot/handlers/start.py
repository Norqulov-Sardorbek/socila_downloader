import os
import logging
from glob import glob
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, 
    CallbackQuery,
    ReplyKeyboardRemove,
    ContentType,
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.utils.ratelimit import RateLimiter
from yt_dlp import YoutubeDL
from dispatcher import dp
from bot.buttons.inline import join_channels
from bot.buttons.reply import *
from bot.state.main import *
from bot.utils import check_user_subscription, convert_to_round

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
rate_limiter = RateLimiter(rate=1, burst=5)
dp.message.middleware(rate_limiter)

# Ensure directories exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Global cache for video info
video_info_cache = {}

@dp.message(Command("about"), StateFilter(None))
async def about(message: Message, state: FSMContext) -> None:
    await message.answer("This bot can download videos from YouTube and Instagram and convert videos to round format.")

@dp.message(Command("start"), StateFilter(None))
async def start(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    await state.update_data(tg_id=tg_id)
    
    if not await check_user_subscription(tg_id):
        await message.answer(
            text=f"Hello {message.from_user.first_name}!\n\nPlease subscribe to our channel to use the bot:",
            reply_markup=join_channels()
        )
        return
    
    await message.answer(
        text="✅ Welcome! You can now send videos or YouTube/Instagram links.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.callback_query(F.data == "check_subscription")
async def handle_sub_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.delete()
    
    data = await state.get_data()
    tg_id = data.get('tg_id')
    
    if not await check_user_subscription(tg_id):
        await callback.message.answer(
            text="🚫 You haven't subscribed to our channel yet.",
            reply_markup=join_channels()
        )
    else:
        await callback.message.answer(
            text="✅ Welcome! You can now send videos or YouTube/Instagram links.",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.message(F.content_type.in_([ContentType.VIDEO, ContentType.DOCUMENT]))
async def video_document_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get('tg_id')

    if not await check_user_subscription(tg_id):
        await message.answer(
            text="🚫 You haven't subscribed to our channel yet.",
            reply_markup=join_channels()
        )
        return

    file = message.video or message.document
    if not file:
        await message.answer("📹 Please send a video or document.")
        return

    await message.answer("Converting video to round format...")

    file_id = file.file_id
    new_filename = f"{file_id}.mp4"
    raw_path = f"downloads/{new_filename}"
    output_path = f"outputs/round_{new_filename}"

    try:
        # Download file from Telegram
        file_obj = await bot.get_file(file_id)
        await bot.download_file(file_obj.file_path, destination=raw_path)

        # Convert to round
        convert_to_round(raw_path, output_path)

        # Send result
        vid = FSInputFile(output_path)
        await message.answer_video_note(video_note=vid)

    except Exception as e:
        logger.error(f"Video conversion error: {e}")
        await message.answer("❌ Error converting video.")

    finally:
        # Clean up files
        for path in [raw_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(f"Error removing file {path}: {e}")

@dp.message(F.text.startswith(("https://youtu", "https://www.youtube", "https://www.instagram.com")))
async def process_link(message: Message, state: FSMContext):
    chat_id = message.chat.id
    url = message.text

    msg = await message.answer("🔍 Checking available formats...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
        'ignoreerrors': True,
        'ratelimit': 1000000,
        'retries': 3,
        'cookiefile': 'cookies.txt',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get('formats', [])
        title = info.get('title') or "Unknown video"
        video_info_cache[chat_id] = info

        buttons = []
        added_res = set()

        for f in formats:
            if not f.get("format_id"):
                continue

            if f.get("vcodec") == "none":
                continue

            resolution = f.get('format_note') or f.get('height')
            ext = f.get('ext')
            format_id = f.get('format_id')

            if resolution and ext == 'mp4':
                try:
                    if isinstance(resolution, str) and 'p' in resolution.lower():
                        height = int(resolution.lower().replace('p', ''))
                    else:
                        height = int(resolution)
                except (ValueError, TypeError):
                    continue

                if height < 480:
                    continue

                str_res = f"{height}p"
                if str_res not in added_res:
                    added_res.add(str_res)
                    buttons.append([
                        InlineKeyboardButton(
                            text=str_res,
                            callback_data=f"video|{format_id}"
                        )
                    ])

        buttons.append([
            InlineKeyboardButton(text="🎧 MP3 (audio)", callback_data="audio|bestaudio")
        ])

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        await msg.delete()
        await message.answer(
            f"🎬 *{title}*\nSelect download format:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.delete()
        logger.error(f"Format detection error: {e}")
        await message.answer("❌ Could not get video formats. Please try another link.")

@dp.callback_query(F.data.startswith(("video|", "audio|")))
async def download_selected_format(query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()

    if user_id not in video_info_cache:
        await query.message.answer("❌ Video info expired. Please send the link again.")
        return

    try:
        choice_type, format_id = query.data.split('|')
        await query.message.delete()
        downloading_msg = await query.message.answer("⏳ Downloading...")

        info = video_info_cache[user_id]
        url = info.get("webpage_url")
        output_template = 'downloads/%(title).50s.%(ext)s'

        ydl_opts = {
            'format': f'{format_id}+bestaudio/best' if choice_type == "video" else 'bestaudio',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'ratelimit': 1000000,
            'retries': 3,
            'merge_output_format': 'mp4',
            'cookiefile': 'cookies.txt',
            'extract_flat': True,
        }

        if choice_type == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        downloaded_files = sorted(glob("downloads/*.mp*"), key=os.path.getmtime, reverse=True)
        filename = downloaded_files[0] if downloaded_files else None

        if not filename or not os.path.exists(filename):
            await downloading_msg.delete()
            await query.message.answer("❌ File not found.")
            return

        await downloading_msg.delete()
        file = FSInputFile(filename)

        if os.path.getsize(filename) > 50 * 1024 * 1024:  # 50MB limit
            await query.message.answer("❌ File is too large to send via Telegram.")
        else:
            if choice_type == "audio":
                await query.message.answer_audio(audio=file)
            else:
                await query.message.answer_video(video=file)

    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.message.answer(f"❌ Download failed: {str(e)}")

    finally:
        # Clean up files
        for pattern in ["downloads/*.mp*", "downloads/*.part"]:
            for f in glob(pattern):
                try:
                    os.remove(f)
                except Exception as e:
                    logger.error(f"Error removing file {f}: {e}")

        video_info_cache.pop(user_id, None)

async def cleanup():
    """Clean up temporary files"""
    for pattern in ["downloads/*", "outputs/*"]:
        for f in glob(pattern):
            try:
                os.remove(f)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")