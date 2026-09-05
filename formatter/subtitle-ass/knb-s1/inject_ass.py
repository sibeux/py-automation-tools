"""
Script for injecting json dialog format to raw ass subtitle files.
"""

import json
import os

def inject_json_to_ass(ass_filepath, json_filepath, output_filepath):
    if not os.path.exists(ass_filepath):
        print(f"Error: File {ass_filepath} tidak ditemukan.")
        return
    if not os.path.exists(json_filepath):
        print(f"Error: File {json_filepath} tidak ditemukan.")
        return

    # 1. Baca file ASS asli
    with open(ass_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. Baca file JSON yang sudah diterjemahkan
    with open(json_filepath, 'r', encoding='utf-8') as f:
        translated_data = json.load(f)

    # 3. Masukkan teks yang sudah diterjemahkan ke baris yang tepat
    for item in translated_data:
        line_idx = item.get("line_index")
        translated_text = item.get("text")
        
        if line_idx is not None and line_idx < len(lines):
            original_line = lines[line_idx]
            if original_line.startswith("Dialogue:"):
                parts = original_line.strip().split(',', 9)
                if len(parts) == 10:
                    # Ganti teks asli (index 9) dengan teks terjemahan
                    parts[9] = translated_text
                    # Gabungkan kembali menjadi satu baris utuh
                    lines[line_idx] = ",".join(parts) + "\n"

    # 4. Simpan ke file ASS baru
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
    print(f"Berhasil membuat file subtitle terjemahan: {output_filepath}")

if __name__ == "__main__":
    ass_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a.ass"           # File ASS asli
    json_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\subtitle_raw.json"     # File JSON dari AI
    output_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a_result.ass"     # Nama file ASS baru hasil terjemahan
    
    inject_json_to_ass(ass_file, json_file, output_file)
