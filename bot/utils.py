import subprocess
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMember
from dispatcher import bot
from bot.models import ChannelsToSubscribe




async def check_user_subscription(user_id: int) -> bool:
    results = {}
    chat_ids = list(ChannelsToSubscribe.objects.values_list("link", flat=True))
    for chat_id in chat_ids:
        try:
            chat_member: ChatMember = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            subscribed_statuses = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
            results[chat_id] = chat_member.status in subscribed_statuses
        except Exception as e:
            print(f"❌ Error checking {chat_id}: {e}")
            results[chat_id] = False

    return all(results.values())

def convert_to_round(input_path, output_path):
    subprocess.call([
        "ffmpeg", "-i", input_path, "-vf",
        "scale=240:240:force_original_aspect_ratio=decrease,pad=240:240:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-t", "60", "-an", "-y",
        output_path
    ])
    
def remove_at_prefix(chat_id: str) -> str:
    return chat_id.lstrip('@')
