import asyncio
import os
import re
import sys
import io
import time
import base64
import urllib.request
import discord
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Load environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("WARNING: DISCORD_TOKEN tidak ditemukan di file .env!")

app = FastAPI(title="Discord PDF Web Reader API (Streaming / Partial Content)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

bot_ready = asyncio.Event()

# In-Memory Cache agar tidak download berulang-ulang dari CDN Discord
# Format: { str(attachment_id): { "doc": fitz.Document, "total_pages": int, "url": str, "timestamp": float } }
PDF_MEMORY_CACHE = {}
CACHE_TTL = 3600  # 60 Menit


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
    asyncio.create_task(start_bot())


def parse_discord_message_link(link_or_text: str):
    """Mengekstrak channel_id dan message_id dari format link Discord."""
    pattern = r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(?:@me|\d+)/(\d+)/(\d+)"
    match = re.search(pattern, link_or_text.strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def download_pdf_stream(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read()


def get_or_load_pdf(attachment_id: str, url: str):
    """Ambil PDF dari cache in-memory atau download & parse."""
    att_key = str(attachment_id)
    now = time.time()
    if att_key in PDF_MEMORY_CACHE:
        entry = PDF_MEMORY_CACHE[att_key]
        if now - entry["timestamp"] < CACHE_TTL:
            return entry["doc"], entry["total_pages"]

    pdf_bytes = download_pdf_stream(url)
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    PDF_MEMORY_CACHE[att_key] = {
        "doc": doc,
        "total_pages": total_pages,
        "url": url,
        "timestamp": now
    }
    return doc, total_pages


@app.get("/api/pdf")
async def get_pdf_metadata(
    link: str = Query(None, description="Link pesan Discord"),
    channel_id: int = Query(None, description="ID Channel/Thread"),
    message_id: int = Query(None, description="ID Message")
):
    try:
        await asyncio.wait_for(bot_ready.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Bot Discord belum siap.")

    if link:
        c_id, m_id = parse_discord_message_link(link)
        if c_id and m_id:
            channel_id, message_id = c_id, m_id
        else:
            raise HTTPException(status_code=400, detail="Format Link Discord tidak valid.")

    if not channel_id or not message_id:
        raise HTTPException(status_code=400, detail="Masukkan Link Pesan Discord atau Channel ID & Message ID.")

    channel = client.get_channel(channel_id)
    if not channel:
        try:
            channel = await client.fetch_channel(channel_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Channel {channel_id} tidak ditemukan / bot tidak ada akses.")

    try:
        message = await channel.fetch_message(message_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Pesan {message_id} tidak ditemukan: {str(e)}")

    pdf_attachments = [
        att for att in message.attachments
        if (att.filename and att.filename.lower().endswith(".pdf"))
        or (att.content_type and "pdf" in att.content_type.lower())
    ]

    if not pdf_attachments:
        raise HTTPException(status_code=404, detail="Tidak ada attachment file PDF pada pesan ini.")

    results = []
    for att in pdf_attachments:
        att_id_str = str(att.id)
        try:
            doc, total_pages = get_or_load_pdf(att_id_str, att.url)
        except Exception as e:
            print(f"Error loading {att.filename}: {e}")
            total_pages = 0

        results.append({
            "id": att_id_str,
            "filename": att.filename,
            "url": att.url,
            "size": att.size,
            "total_pages": total_pages
        })

    return {
        "success": True,
        "channel_id": str(channel_id),
        "message_id": str(message_id),
        "channel_name": getattr(channel, "name", f"Channel {channel_id}"),
        "author": str(message.author),
        "created_at": message.created_at.isoformat(),
        "pdf_count": len(results),
        "pdfs": results
    }


@app.get("/api/pdf/{attachment_id}/page/{page_number}")
async def get_pdf_page_partial(
    attachment_id: str,
    page_number: int,
    dpi: int = Query(140, description="Kualitas render gambar")
):
    """
    Partial Content Endpoint:
    Render 1 halaman langsung dari PDF_MEMORY_CACHE tanpa perlu fetch channel lagi.
    """
    att_key = str(attachment_id)

    if att_key not in PDF_MEMORY_CACHE:
        raise HTTPException(
            status_code=404, 
            detail="Session dokumen telah kedaluwarsa atau belum dimuat. Silakan muat ulang dokumen dari kolom input."
        )

    doc = PDF_MEMORY_CACHE[att_key]["doc"]
    total_pages = PDF_MEMORY_CACHE[att_key]["total_pages"]

    if page_number < 1 or page_number > total_pages:
        raise HTTPException(status_code=400, detail=f"Nomor halaman di luar jangkauan (1-{total_pages}).")

    try:
        page = doc[page_number - 1]
        text = page.get_text()

        # Render halaman menjadi gambar PNG
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        img_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

        return {
            "page_number": page_number,
            "total_pages": total_pages,
            "width": page.rect.width,
            "height": page.rect.height,
            "image": img_b64,
            "text": text.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal me-render halaman {page_number}: {str(e)}")


# Mount static files (Frontend Web App)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Memulai server FastAPI Discord PDF Reader di http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
