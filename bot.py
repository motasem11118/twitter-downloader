import os
import re
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Health Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل رابط فيديو من X أو Twitter وسأحاول تنزيله."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text.strip()

    if not re.search(r"(x\.com|twitter\.com)", url):
        return

    msg = await update.message.reply_text("⏳ جاري التنزيل...")

    try:

        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "noplaylist": True,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.edit_text("📤 جاري رفع الفيديو...")

        with open(filename, "rb") as video:
            await update.message.reply_video(video=video)

        os.remove(filename)

        await msg.delete()

    except Exception as e:
        logging.error(str(e))
        await msg.edit_text(f"❌ فشل التنزيل\n{e}")

def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            download_video
        )
    )

    app.run_polling()

if __name__ == "__main__":
    main()
