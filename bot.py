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

# سيرفر وهمي للحفاظ على استقرار منصة Render ومنع الإغلاق
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
    await update.message.reply_text("💪 بوت ملاذ المطور جاهز وسريع! أرسل أي رابط فيديو من منصة X (تويتر) وسيتم رفعه لك كملف مباشرة.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    status_message = await update.message.reply_text("⏳ جاري المعالجة والرفع المباشر كملف، انتظر ثوانٍ...")

    # تنظيف الرابط من أي إضافات تتبع أو صيغ جوال مختصرة وتوحيدها
    tweet_id_match = re.search(r'status/(\d+)', url)
    if tweet_id_match:
        url = f"https://x.com/i/status/{tweet_id_match.group(1)}"

    # استخدام خادم ومحرك Cobalt العالمي لمعالجة وتجاوز حظر تويتر
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "videoQuality": "max", 
        "filenamePattern": "classic"
    }

    try:
        # إرسال الطلب لمحرك التحميل السريع
        response = requests.post("https://api.cobalt.tools/", json=payload, headers=headers, timeout=12)
        result = response.json()

        # إذا نجح في جلب رابط الفيديو المباشر النظيف
        if result.get("status") == "stream" or result.get("status") == "picker":
            video_url = result.get("url")
            
            # إرسال الفيديو فوراً للمستخدم كملف فيديو كامل داخل تلجرام
            await update.message.reply_video(video=video_url, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
            await status_message.delete()
        else:
            raise Exception("Cobalt failed to get stream URL")

    except Exception as e:
        logger.error(f"Error logic: {e}")
        # خطة احتياطية سريعة ومضمونة في حال تعطل خوادم الرفع
        fallback = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 تعذر الرفع المباشر كملف، يمكنك مشاهدة وحفظ الفيديو فوراً عبر هذا الرابط البديل:\n\n🔗 {fallback}")

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
