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
    await update.message.reply_text("💪 بوت ملاذ جاهز وسريع بأعلى كفاءة! أرسل أي رابط فيديو من منصة X (تويتر) وسيتم رفعه لك مباشرة كملف فيديو داخل المحادثة.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    status_message = await update.message.reply_text("⏳ جاري استخراج وتحميل الفيديو مباشرة، انتظر ثوانٍ...")

    try:
        # استخدام API وسيط قوي لتجاوز حظر خوادم تويتر تماماً
        api_url = f"https://twitsave.com/info?url={url}"
        response = requests.get(api_url, timeout=15)
        html_content = response.text

        # البحث عن رابط تحميل ملف الـ MP4 المباشر من صفحة twitsave
        download_match = re.search(r'href="(https://[^"]+extid[^"]+)"', html_content)
        
        if not download_match:
            # محاولة ثانية بنمط مختلف للرابط
            download_match = re.search(r'href="(https://twitsave\.com/download[^"]+)"', html_content)

        if download_match:
            video_url = download_match.group(1).replace("&amp;", "&")
            
            # إرسال الفيديو مباشرة إلى تلجرام عبر الرابط المستخرج دون استهلاك مساحة السيرفر
            await update.message.reply_video(video=video_url, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
            await status_message.delete()
        else:
            raise Exception("تعذر العثور على رابط تحميل مباشر")

    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        # إذا تعطل الـ API تماماً، نستخدم الخيار السريع والمضمون للمشاهدة
        fallback = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"🎬 تعذر الرفع المباشر كملف بسبب قيود المنصة، ولكن يمكنك مشاهدة وحفظ الفيديو مباشرة من هنا:\n\n🔗 {fallback}")

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
