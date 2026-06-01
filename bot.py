import os
import re
import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# سيرفر وهمي للحفاظ على استقرار منصة Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💪 بوت ملاذ جاهز وسريع! أرسل أي رابط من منصة X (تويتر) وسيتم رفعه لك مباشرة كملف فيديو داخل المحادثة.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    status_message = await update.message.reply_text("⏳ جاري استخراج وتحميل الفيديو، انتظر ثوانٍ...")

    # إعدادات قوية جداً لـ yt-dlp تضمن فك التشفير للروابط المختصرة والمحتوى المقيد
    ydl_opts = {
        'format': 'bestsingle / bestvideo+bestaudio/best',
        'no_warnings': True,
        'quiet': True,
        'age_limit': 99,
        'skip_download': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # محاولة جلب الرابط المباشر بأكثر من طريقة لضمان الملف
            video_url = None
            if 'url' in info:
                video_url = info['url']
            elif 'entries' in info and len(info['entries']) > 0:
                video_url = info['entries'][0].get('url')
            elif 'formats' in info and len(info['formats']) > 0:
                video_url = info['formats'][-1].get('url')

            if video_url:
                # إرسال الفيديو مباشرة باستخدام رابط البث لتجنب مشاكل حجم خوادم ريندر
                await update.message.reply_video(video=video_url, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
                await status_message.delete()
            else:
                raise Exception("No direct video url found")
                
    except Exception as e:
        logger.error(f"Download Error: {e}")
        # إذا فشل السيرفر تماماً، يتم تقديم الرابط السريع كخيار بديل فوري
        fallback = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 عذراً، هذا الفيديو محمي بشكل كامل أو حجمه كبير، يمكنك مشاهدته وحفظه مباشرة من الرابط التالي:\n\n🔗 {fallback}")

def main():
    if not BOT_TOKEN: 
        return
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_twitter_video))
    app.run_polling()

if __name__ == '__main__':
    main()
