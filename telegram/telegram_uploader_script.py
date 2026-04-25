"""
Uploader audio ke topic Telegram.
"""
from dotenv import load_dotenv
import shutil
import requests
import os
import time

load_dotenv()

# --- KONFIGURASI ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # e.g. -1001234567890
THREAD_ID = int(os.getenv("TELEGRAM_THREAD_ID")) # message_thread_id topic
FOLDER_PATH = rf"C:\Users\Nasrul Wahabi\Downloads\Music\UPLOAD\2-Anisong\2-coolest-20260422-201012\flac"
DELAY = 5  # Detik antar upload
# -------------------

ekstensi = ('.mp3', '.m4a', '.ogg', '.flac', '.wav', '.aac')

LARGE_FILES_FOLDER = os.path.join(FOLDER_PATH, "large_files")
os.makedirs(LARGE_FILES_FOLDER, exist_ok=True)

MAX_SIZE = 50 * 1024 * 1024  # 50 MB (batas Telegram Bot API)


def upload_audio(file_path: str, filename: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    with open(file_path, "rb") as f:
        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "message_thread_id": THREAD_ID,
        }, files={
            "audio": (filename, f),
        })
    return response.json()


def main():
    # Ambil semua file audio
    all_files = []
    for f in os.listdir(FOLDER_PATH):
        if f.lower().endswith(ekstensi):
            full_path = os.path.join(FOLDER_PATH, f)
            try:
                file_size = os.path.getsize(full_path)
                if file_size <= MAX_SIZE:
                    all_files.append(f)
                else:
                    dest_path = os.path.join(LARGE_FILES_FOLDER, f)
                    shutil.move(full_path, dest_path)
                    size_mb = file_size / (1024 * 1024)
                    print(f"Dipindahkan {f}: Ukuran {size_mb:.2f} MB → {LARGE_FILES_FOLDER}")
            except OSError as e:
                print(f"Error mengakses {f}: {e}")

    all_files.sort()
    print(f"Ditemukan {len(all_files)} audio. Memulai upload...")

    # Upload satu per satu (Telegram tidak support batch attach seperti Discord)
    for index, filename in enumerate(all_files):
        full_path = os.path.join(FOLDER_PATH, filename)
        try:
            result = upload_audio(full_path, filename)
            if result.get("ok"):
                print(f"[{index + 1}/{len(all_files)}] Terkirim: {filename}")
            else:
                print(f"[{index + 1}/{len(all_files)}] Gagal: {filename} → {result.get('description')}")
        except Exception as e:
            print(f"Error pada {filename}: {e}")

        time.sleep(DELAY)

    print("Selesai semua upload!")


if __name__ == "__main__":
    main()