"""
Reader gambar/video dari thread Discord.
"""

import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
THREAD_ID = int(input("Masukkan THREAD ID: "))

class ComicReader(discord.Client):
    async def on_ready(self):
        print(f'Login sebagai {self.user}')
        thread = self.get_channel(THREAD_ID)

        if not thread:
            print("Thread tidak ditemukan!")
            await self.close()
            return

        all_pages = []

        print("Sedang mengambil pesan...")
        # Mengambil semua pesan dari thread
        async for message in thread.history(limit=200, oldest_first=True):
            if message.attachments:
                for attachment in message.attachments:
                    # Filter hanya file gambar
                    if attachment.content_type and attachment.content_type.startswith('image'):
                        all_pages.append({
                            "filename": attachment.filename,
                            "url": attachment.url
                        })

        # Mengurutkan berdasarkan nama file (penting jika uploadnya per batch)
        # Agar halaman 1.png, 2.png dst berurutan
        all_pages.sort(key=lambda x: x['filename'])

        print(f"\n--- Ditemukan {len(all_pages)} Halaman Komik ---\n")
        
        # Output dalam format JSON atau List URL untuk Web
        for page in all_pages:
            print(f"{page['filename']}: {page['url']}")

        await self.close()

# Perlu Intents History untuk membaca pesan lama
intents = discord.Intents.default()
intents.message_content = True # Baris ini yang meminta izin baca pesan
intents.members = True # Opsional, tapi baik untuk sinkronisasi thread

client = ComicReader(intents=intents)
client.run(TOKEN)