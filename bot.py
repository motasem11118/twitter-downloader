import os
import yt_dlp

async def download_twitter_video(update, context):
    url = update.message.text.strip()

    msg = await update.message.reply_text("⏳ جاري التنزيل...")

    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.edit_text("📤 جاري رفع الفيديو...")

        with open(filename, "rb") as video:
            await update.message.reply_video(video=video)

        os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"❌ فشل التنزيل:\n{e}")
