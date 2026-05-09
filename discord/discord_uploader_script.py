"""
Uploader gambar/video ke thread Discord.
"""

from dotenv import load_dotenv
import shutil
import discord
import os
import asyncio
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

load_dotenv()  # otomatis baca file .env di direktori sekarang

# --- KONFIGURASI ---
TOKEN = os.getenv("DISCORD_TOKEN")

try:
    THREAD_ID = int(input("Masukkan THREAD ID: ").strip())
    FOLDER_PATH = input("Masukkan PATH FOLDER: ").strip().strip('"').strip("'")
except ValueError:
    print("Error: THREAD ID harus berupa angka!")
    exit()

if not os.path.isdir(FOLDER_PATH):
    print(f"Error: Folder tidak ditemukan: {FOLDER_PATH}")
    exit()

DELAY = 5  # Detik

EKSTENSI_GROUPS = [
    ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.heic'),
    ('.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.m4a'),
    ('.pdf',)
]

LARGE_FILES_FOLDER = os.path.join(FOLDER_PATH, "large_files")
# Buat folder large_files jika belum ada
os.makedirs(LARGE_FILES_FOLDER, exist_ok=True)

class BatchUploader(discord.Client):
    async def on_ready(self):
        print(f'Login sebagai {self.user}')
        thread = self.get_channel(THREAD_ID)
        print(thread)

        if not thread:
            print("Thread tidak ditemukan! Cek ID lagi.")
            await self.close()
            return

        # Ambil semua file gambar/video
        MAX_SIZE = 10 * 1024 * 1024  # 10 MB dalam bytes

        for current_ext in EKSTENSI_GROUPS:
            print(f"\n--- Memproses kategori: {current_ext} ---")
            all_files = []

            for f in os.listdir(FOLDER_PATH):
                # Cek ekstensi
                if f.lower().endswith(current_ext):
                    full_path = os.path.join(FOLDER_PATH, f)
                    # Cek ukuran file (<= 10 MB)
                    try:
                        file_size = os.path.getsize(full_path)
                        if file_size <= MAX_SIZE:
                            all_files.append(f)
                        else:
                            # Pindahkan file ke folder large_files
                            dest_path = os.path.join(LARGE_FILES_FOLDER, f)
                            shutil.move(full_path, dest_path)
                            size_mb = file_size / (1024 * 1024)
                            print(
                                f"Dipindahkan {f}: Ukuran {size_mb:.2f} MB → {LARGE_FILES_FOLDER}")
                    except OSError as e:
                        print(f"Error mengakses {f}: {e}")

            all_files.sort(key=natural_sort_key)  # Urutkan nama file secara natural

            if not all_files:
                print(f"Tidak ada file untuk kategori {current_ext}.")
                continue

            print(f"Ditemukan {len(all_files)} file. Memulai upload...")

            # Memecah list menjadi potongan (chunks) isi 10
            chunks = [all_files[i:i + 10] for i in range(0, len(all_files), 10)]

            for index, chunk in enumerate(chunks):
                files_to_send = []
                try:
                    # Siapkan 10 file (atau sisa file) untuk di-attach
                    for filename in chunk:
                        path = os.path.join(FOLDER_PATH, filename)
                        files_to_send.append(discord.File(path))

                    # Kirim 1 pesan berisi banyak file
                    await thread.send(files=files_to_send)

                    print(
                        f'Batch {index + 1}/{len(chunks)} terkirim ({len(chunk)} file).')

                    # Jeda aman
                    await asyncio.sleep(DELAY)

                except Exception as e:
                    print(f'Error pada batch {index + 1}: {e}')

                finally:
                    # Bersihkan memori file handle
                    for f in files_to_send:
                        f.close()

        print("Selesai semua upload!")
        await self.close()

intents = discord.Intents.default()
client = BatchUploader(intents=intents)
client.run(TOKEN)
