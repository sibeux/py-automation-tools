"""
Uploader folder audio ke thread Discord.
"""

from dotenv import load_dotenv
import shutil
import discord
import os
import asyncio
import re
import datetime

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

MONTHS_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

def get_file_date_str(path):
    try:
        ts = os.path.getmtime(path)
        dt = datetime.datetime.fromtimestamp(ts)
        return f"{dt.day} {MONTHS_ID[dt.month]} {dt.year}"
    except Exception:
        return "Unknown"

load_dotenv()  # otomatis baca file .env di direktori sekarang

# --- KONFIGURASI ---
TOKEN = os.getenv("DISCORD_TOKEN")

try:
    THREAD_ID = int(input("Masukkan THREAD ID: ").strip())
    FOLDER_PATH = input("Masukkan PATH FOLDER UTAMA: ").strip().strip('"').strip("'")
except ValueError:
    print("Error: THREAD ID harus berupa angka!")
    exit()

if not os.path.isdir(FOLDER_PATH):
    print(f"Error: Folder tidak ditemukan: {FOLDER_PATH}")
    exit()

DELAY = 5  # Detik
AUDIO_EXTENSIONS = ('.opus', '.ogg', '.wav', '.mp3', '.m4a')
LARGE_FILES_FOLDER = os.path.join(FOLDER_PATH, "large_files")
os.makedirs(LARGE_FILES_FOLDER, exist_ok=True)

class BatchUploader(discord.Client):
    async def on_ready(self):
        print(f'Login sebagai {self.user}')
        thread = self.get_channel(THREAD_ID)
        
        if not thread:
            print("Thread tidak ditemukan! Cek ID lagi.")
            await self.close()
            return

        # Ambil semua subfolder, kecualikan 'large_files'
        try:
            subdirs = [d for d in os.listdir(FOLDER_PATH) 
                    if os.path.isdir(os.path.join(FOLDER_PATH, d)) and d.lower() != "large_files"]
            # Urutkan subfolder berdasarkan waktu modifikasi dari yang terlama ke terbaru
            subdirs.sort(key=lambda d: os.path.getmtime(os.path.join(FOLDER_PATH, d)))
        except Exception as e:
            print(f"Error saat mengakses folder: {e}")
            await self.close()
            return

        MAX_SIZE = 10 * 1024 * 1024  # 10 MB dalam bytes

        print(f"Ditemukan {len(subdirs)} folder untuk diproses.\n")

        for subdir in subdirs:
            current_dir = os.path.join(FOLDER_PATH, subdir)
            print(f"--- Memproses Folder: {subdir} ---")
            
            all_files = []
            try:
                for f in os.listdir(current_dir):
                    if f.lower().endswith(AUDIO_EXTENSIONS):
                        full_path = os.path.join(current_dir, f)
                        if not os.path.isfile(full_path):
                            continue
                        try:
                            file_size = os.path.getsize(full_path)
                            if file_size <= MAX_SIZE:
                                all_files.append(f)
                            else:
                                # Pindahkan file ke subfolder large_files terisolasi agar tidak menimpa file bernama sama dari folder lain
                                dest_subdir = os.path.join(LARGE_FILES_FOLDER, subdir)
                                os.makedirs(dest_subdir, exist_ok=True)
                                dest_path = os.path.join(dest_subdir, f)
                                shutil.move(full_path, dest_path)
                                size_mb = file_size / (1024 * 1024)
                                print(f"    [Besar] Dipindahkan {f}: Ukuran {size_mb:.2f} MB → {dest_subdir}")
                        except OSError as e:
                            print(f"    Error mengakses {f}: {e}")
            except OSError as e:
                print(f"    Gagal membaca isi folder {subdir}: {e}")
                continue

            all_files.sort(key=natural_sort_key)  # Urutkan nama file secara natural

            if not all_files:
                print(f"    Tidak ada file audio di folder ini.\n")
                continue

            print(f"    Ditemukan {len(all_files)} file audio. Memulai upload...")

            # Memecah list menjadi potongan (chunks) isi 10
            chunks = [all_files[i:i + 10] for i in range(0, len(all_files), 10)]

            for index, chunk in enumerate(chunks):
                files_to_send = []
                try:
                    for filename in chunk:
                        path = os.path.join(current_dir, filename)
                        files_to_send.append(discord.File(path))

                    # Ambil tanggal file pertama dan terakhir di batch ini
                    first_path = os.path.join(current_dir, chunk[0])
                    last_path = os.path.join(current_dir, chunk[-1])
                    first_date = get_file_date_str(first_path)
                    last_date = get_file_date_str(last_path)
                    
                    # Template Caption: {nama folder / Batch n / Tanggal file pertama - tanggal file terakhir}
                    caption = f"{subdir} / Batch {index + 1} / {first_date} - {last_date}"

                    # Kirim pesan berisi caption dan lampiran files
                    await thread.send(content=caption, files=files_to_send)

                    print(f'    Batch {index + 1}/{len(chunks)} terkirim.')
                    
                    # Jeda aman agar tidak terkena limit rate discord
                    await asyncio.sleep(DELAY)

                except Exception as e:
                    print(f'    Error pada batch {index + 1}: {e}')

                finally:
                    for f in files_to_send:
                        f.close()
            print(f"Selesai memproses folder: {subdir}\n")

        print("Semua folder selesai diupload!")
        await self.close()

intents = discord.Intents.default()
client = BatchUploader(intents=intents)
client.run(TOKEN)
