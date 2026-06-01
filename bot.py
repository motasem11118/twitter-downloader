import os
import re
import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات لمراقبة العمليات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- 1. خدعة منفذ الويب الوهمي لمنع Render من إغلاق البوت ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Fake Web Server listening on port {port}")
    server.serve_forever()

# --- 2. منطق تشغيل البوت وتحميل الفيديوهات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💪 بوت ملاذ جاهز بكامل طاقته السحابية! أرسل أي رابط من منصة X (تويتر)، بما في ذلك الروابط المختصرة أو المحتوى الحساس، وسيتم رفعه لك مباشرة.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    status_message = await update.message.reply_text("⏳ جاري معالجة وتحميل الفيديو، انتظر ثوانٍ...")

    # معالجة وتحويل الروابط المختصرة (مثل x.com/i/status) إلى صيغة صريحة يفهمها السيرفر
    if "/i/status/" in url:
        url = re.sub(r'x\.com/i/status/(\d+)', r'x.com/x/status/\1', url)
        url = re.sub(r'twitter\.com/i/status/(\d+)', r'twitter.com/x/status/\1', url)
    
    # تنظيف روابط المواقع البديلة لتوحيد المسار
    url = url.replace("fxfxtwitter.com", "x.com").replace("vxtwitter.com", "x.com")

    # إعدادات متقدمة لـ yt-dlp لتخطي قيود العمر والمحتوى المقيد بالسن
    ydl_opts = {
        'format': 'best',
        'no_warnings': True,
        'quiet': True,
        'age_limit': 99,  # تخطي قيود المحتوى الحساس والسن تماماً
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
                # تحميل الفيديو كبث وإرساله مباشرة دون تخزين طويل
                video_data = requests.get(video_url, stream=True).content
                await update.message.reply_video(video=video_data, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
                await status_message.delete()
            else:
                raise Exception("لم يتم العثور على رابط مباشر")
                
    except Exception as e:
        logger.error(f"Error during download: {e}")
        # خيار احتياطي في حال وجود حظر جرافي للـ IP الخاص بالسيرفر من تويتر
        fallback_url = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 تعذر الرفع المباشر كملف بسبب قيود حجم خوادم المنصة، ولكن يمكنك مشاهدة الفيديو وتحميله بدون قيود عبر الرابط التالي:\n\n🔗 {fallback_url}")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return

    # بدء السيرفر الوهمي في مسار منفصل لمنع التجميد
    threading.Thread(target=run_health_server, daemon=True).start()
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_twitter_video))
    
    logger.info("Bot polling deployed successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
