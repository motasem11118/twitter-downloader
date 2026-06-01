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
    await update.message.reply_text("💪 بوت ملاذ جاهز بكامل طاقته السحابية! أرسل أي رابط من منصة X (تويتر)، بما في ذلك الروابط المختصرة أو المحتوى الحساس، وسيتم رفعه لك مباشرة كملف فيديو.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    original_url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', original_url):
        return

    status_message = await update.message.reply_text("⏳ جاري سحب وتجهيز الفيديو، انتظر ثوانٍ...")

    # استخراج الرقم التعريفي للفيديو بدقة لتخطي الروابط المختصرة (مثل i/status أو أي صيغة جوال)
    tweet_id_match = re.search(r'status/(\d+)', original_url)
    if tweet_id_match:
        tweet_id = tweet_id_match.group(1)
        url = f"https://x.com/i/status/{tweet_id}"
    else:
        url = original_url

    # إعدادات متطورة ومجربة لتجاوز حظر المحتوى +18 والروابط الحساسة
    ydl_opts = {
        'format': 'best',
        'no_warnings': True,
        'quiet': True,
        'age_limit': 99,  # كسر قيود العمر نهائياً
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            
            if video_url:
                # تحميل الملف كبث ورفعه مباشرة لتلجرام بصيغة MP4
                video_data = requests.get(video_url, stream=True).content
                await update.message.reply_video(video=video_data, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
                await status_message.delete()
            else:
                raise Exception()
                
    except Exception as e:
        logger.error(f"Error: {e}")
        # خطة احتياطية في حال تعطل الصيغة المباشرة تماماً
        fallback = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 تعذر الرفع المباشر كملف، يمكنك مشاهدة وحفظ الفيديو بدون قيود عبر هذا الرابط البديل:\n\n🔗 {fallback}")

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
