import os
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = "8976838288:AAHJKjxB2myyGhxGblXyG2Czl19a80pazT4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔓 البوت يعمل سحابياً بكفاءة كاملة! أرسل الرابط بدون قيود.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "x.com" not in url.lower() and "twitter.com" not in url.lower():
        await update.message.reply_text("⚠️ يرجى إرسال رابط إكس صحيح.")
        return

    status_message = await update.message.reply_text("🔓 جاري كسر القيود وسحب الفيديو... ⏳")
    modified_url = re.sub(r'(x\.com|twitter\.com)', 'fxtwitter.com', url, flags=re.IGNORECASE)

    ydl_opts = {
        'format': 'best/bestvideo+bestaudio/any',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'quiet': True,
        'age_limit': 99,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(modified_url, download=True))
            if not info or ('entries' in info and not info['entries']):
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            if info and 'entries' in info:
                info = info['entries'][0]
            filename = ydl.prepare_filename(info)

        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            await status_message.edit_text("📤 جاري الرفع إلى تلجرام...")
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file, supports_streaming=True)
            os.remove(filename)
            await status_message.delete()
        else:
            raise Exception("فشل التحميل")
    except Exception as e:
        direct_stream = url.replace("x.com", "fxtwitter.com").replace("twitter.com", "fxtwitter.com")
        await status_message.edit_text(f"⚠️ تعذر الرفع المباشر، شاهد الفيديو بدون حجب هنا:\n\n🔗 {direct_stream}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("🚀 يعمل بكفاءة...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
