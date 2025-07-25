from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from yt_dlp import YoutubeDL
from dispatcher import dp
import os
from glob import glob

video_info_cache = {}


@dp.message(F.text.startswith(("https://youtu", "https://www.youtube", "https://www.instagram.com")))
async def process_link(message: Message, state: FSMContext):
    chat_id = message.chat.id
    url = message.text

    msg = await message.answer("🔍 Formatlar aniqlanmoqda...")

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'cookiesfrombrowser': ('chrome',),  # cookie ni avtomatik oladi
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get('formats', [])
        title = info.get('title') or "Noma'lum video"
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
            f"🎬 *{title}*\nQaysi formatda yuklab olishni tanlang:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.delete()
        await message.answer("❌ Formatlarni aniqlashda xatolik yuz berdi.\n\n📌 *Instagram videolari uchun siz Chrome orqali Instagram akkauntingizga login bo‘lgan bo‘lishingiz kerak.*", parse_mode="Markdown")
        print("Format aniqlash xatosi:", e)


@dp.callback_query(F.data.startswith(("video|", "audio|")))
async def download_selected_format(query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()

    if user_id not in video_info_cache:
        await query.message.answer("❌ Video ma'lumotlari topilmadi. Qayta link yuboring.")
        return

    filename = None

    try:
        choice_type, format_id = query.data.split('|')
        await query.message.delete()
        downloading_msg = await query.message.answer("⏳ Yuklab olinmoqda...")

        info = video_info_cache[user_id]
        url = info.get("webpage_url")
        output_template = 'downloads/%(title).50s.%(ext)s'

        if choice_type == "audio":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': output_template,
                'quiet': True,
                'restrictfilenames': True,
                'cookiesfrombrowser': ('chrome',),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            ydl_opts = {
                'format': f'{format_id}+bestaudio/best',
                'outtmpl': output_template,
                'quiet': True,
                'restrictfilenames': True,
                'merge_output_format': 'mp4',
                'cookiesfrombrowser': ('chrome',),
            }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        downloaded_files = sorted(glob("downloads/*.mp*"), key=os.path.getmtime, reverse=True)
        filename = downloaded_files[0] if downloaded_files else None

        if not filename or not os.path.exists(filename):
            await downloading_msg.delete()
            await query.message.answer("❌ Faylni topib bo‘lmadi.")
            return

        await downloading_msg.delete()
        file = FSInputFile(filename)
        print("Fayl hajmi:", os.path.getsize(filename) / (1024 * 1024), "MB")

        if choice_type == "audio":
            await query.message.answer_audio(audio=file)
        else:
            await query.message.answer_video(video=file)

    except Exception as e:
        await query.message.answer("❌ Yuklab olishda xatolik yuz berdi.")
        print("Yuklash xatosi:", e)

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as remove_error:
                print("❌ Faylni o‘chirishda xatolik:", remove_error)

        video_info_cache.pop(user_id, None)