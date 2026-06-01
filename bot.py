import os
import re
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات لمراقبة الأخطاء في Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN") # تأكد من ضبط هذا المتغير في إعدادات Render

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💪 البوت يعمل بأقصى كفاءة سحابية! أرسل أي رابط من منصة X (تويتر) وسيتم تحميل الفيديو مباشرة بدون قيود أو حجب المحتوى الحساس.")

async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # التحقق من أن الرابط ينتمي لمنصة تويتر أو إكس
    if not re.search(r'(twitter\.com|x\.com)', url):
        return

    # 1. تنظيف وتحويل الروابط المختصرة (مثل x.com/i/status) إلى الروابط الصريحة لتجنب مشاكل التوجيه
    if "/i/status/" in url:
        url = url.replace("x.com/i/status/", "x.com/x/status/").replace("twitter.com/i/status/", "twitter.com/x/status/")
    
    # تحويل الرابط البديل fxfxtwitter إلى x لتفادي مشاكل الـ DNS في السيرفر
    url = url.replace("fxfxtwitter.com", "x.com").replace("vxtwitter.com", "x.com")

    status_message = await update.message.reply_text("⏳ جاري سحب وتجهيز الفيديو، انتظر ثوانٍ...")

    # 2. إعدادات خيارات yt-dlp لتخطي القيود والمحتوى المقيد بالسن +18
    ydl_opts = {
        'format': 'best',
        'no_warnings': True,
        'quiet': True,
        'age_limit': 99,  # تخطي قيود السن والمحتوى الحساس نهائياً
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            
            if video_url:
                # تحميل الفيديو كملف مؤقت وإرساله مباشرة كـ MP4
                video_data = requests.get(video_url, stream=True).content
                await update.message.reply_video(video=video_data, caption="🎬 تم التحميل بنجاح بواسطة بوت ملاذ.")
                await status_message.delete()
            else:
                raise Exception("فشل في استخراج الرابط المباشر")
                
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        # إذا فشل التحميل المباشر بسبب حظر الآيبي، يرسل رابط المعاينة البديل كخطة احتياطية
        fallback_url = url.replace("x.com", "fxfxtwitter.com").replace("twitter.com", "fxfxtwitter.com")
        await status_message.edit_text(f"⚠️ تعذر الرفع المباشر بسبب قيود السيرفر، يمكنك مشاهدة أو حفظ الفيديو من هذا الرابط بدون حجب:\n\n🔗 {fallback_url}")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_twitter_video))
    
    logger.info("Bot started successfully on Render...")
    app.run_polling()

if __name__ == '__main__':
    main()
