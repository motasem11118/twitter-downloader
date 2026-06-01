import os
import re
import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# سيرفر الحفاظ على استقرار واستمرار الخدمة في Render
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
    await update.message.reply_text("💪 بوت ملاذ جاهز! أرسل أي رابط فيديو من منصة X (تويتر) وسيتم رفعه لك مباشرة داخل المحادثة كملف فيديو.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    status_message = await update.message.reply_text("⏳ جاري سحب وتحميل الفيديو مباشرة إلى تلجرام...")

    # تنظيف وتوحيد روابط تويتر لضمان قبولها في محرك السحب
    tweet_id_match = re.search(r'status/(\d+)', url)
    if tweet_id_match:
        url = f"https://x.com/i/status/{tweet_id_match.group(1)}"

    payload = {
        "url": url,
        "videoQuality": "max", 
        "filenamePattern": "classic"
    }

    try:
        # استدعاء محرك Cobalt العالمي لكسر حماية وحظر تويتر وجلب الرابط الصريح
        response = requests.post("https://api.cobalt.tools/", json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=190)
        result = response.json()

        if result.get("status") == "stream":
            video_url = result.get("url")
            
            # الخدعة الكبرى: تمرير الرابط المباشر لتلجرام ليقوم بمعالجته ورفعه كملف مدمج داخل الشات فوراً
            await update.message.reply_video(video=video_url, caption="🎬 تم التحميل بنجاح داخل تلجرام بواسطة بوت ملاذ.")
            await status_message.delete()
        else:
            raise Exception("Cobalt stream parsing failed")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        # خطة طوارئ سريعة للمشاهدة بدون الخروج من التلجرام في حال حدوث ضغط على السيرفر
        fallback = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 تعذر رفع الفيديو كملف حالياً، ولكن يمكنك تشغيله ومشاهدته مباشرة داخل تلجرام عبر هذا الرابط البديل:\n\n🔗 {fallback}")

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
