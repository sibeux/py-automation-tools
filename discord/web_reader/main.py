import asyncio
import re
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import discord
from dotenv import load_dotenv
import os
import sys

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# Load .env file (looks in current and parent directories)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("WARNING: DISCORD_TOKEN tidak ditemukan di file .env!")

app = FastAPI(title="Discord Comic Reader API")

# Izinkan CORS agar frontend bisa memanggil backend dari origin mana pun
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi Discord Client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

bot_ready = asyncio.Event()

@client.event
async def on_ready():
    print(f"\n==========================================")
    print(f"🤖 Bot Discord berhasil login sebagai: {client.user}")
    print(f"==========================================\n")
    bot_ready.set()

async def start_bot():
    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"❌ Gagal menjalankan Bot Discord: {e}", file=sys.stderr)

@app.on_event("startup")
async def startup_event():
    # Jalankan bot di background task agar tidak memblock FastAPI
    asyncio.create_task(start_bot())

@app.get("/api/comic/{thread_id}")
async def get_comic_pages(thread_id: int):
    # Tunggu bot siap maksimal 10 detik
    try:
        await asyncio.wait_for(bot_ready.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Bot Discord membutuhkan waktu terlalu lama untuk login. Periksa koneksi internet atau token di .env.")
    
    # Cari channel/thread berdasarkan ID
    channel = client.get_channel(thread_id)
    if not channel:
        try:
            channel = await client.fetch_channel(thread_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Thread atau Channel tidak ditemukan. Pastikan Bot sudah diundang ke server tersebut dan memiliki akses membaca channel ini. Error: {str(e)}")
            
    # Validasi tipe channel
    if not isinstance(channel, (discord.Thread, discord.TextChannel, discord.ForumChannel)):
        raise HTTPException(status_code=400, detail="ID tersebut bukan merupakan Text Channel atau Thread.")
        
    all_pages = []
    try:
        # Batasi pengambilan riwayat pesan (bisa diatur sesuai kebutuhan)
        print(f"Fetching messages for channel: {channel.name} (ID: {thread_id})...")
        async for message in channel.history(limit=300, oldest_first=True):
            if message.attachments:
                for attachment in message.attachments:
                    # Filter file gambar
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        all_pages.append({
                            "filename": attachment.filename,
                            "url": attachment.url,
                            "size": attachment.size,
                            "width": attachment.width,
                            "height": attachment.height,
                            "timestamp": message.created_at.isoformat()
                        })
        
        # Sortir file gambar secara alami (Natural Sorting) agar berurutan (misal: 1.jpg, 2.jpg, 11.jpg)
        all_pages.sort(key=lambda x: natural_sort_key(x['filename']))
        
        # Ambil nama parent channel jika ada
        parent_name = None
        if hasattr(channel, 'parent') and channel.parent:
            parent_name = channel.parent.name

        return {
            "success": True,
            "thread_id": thread_id,
            "title": channel.name if hasattr(channel, 'name') else f"Channel {thread_id}",
            "parent_category": parent_name,
            "total_pages": len(all_pages),
            "pages": all_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil riwayat pesan: {str(e)}")

# Mount folder static untuk menyajikan index.html, style.css, script.js
# File index.html akan otomatis disajikan di URL root "/"
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Memulai server FastAPI Comic Reader...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
