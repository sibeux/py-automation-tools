"""
Script for injecting translated JSON dialogue/texts back into the raw ASS subtitle file.
"""

import json
import os

def inject_json_to_ass(ass_filepath, json_filepath, output_filepath):
    if not os.path.exists(ass_filepath):
        print(f"Error: File ASS '{ass_filepath}' tidak ditemukan.")
        return
    if not os.path.exists(json_filepath):
        print(f"Error: File JSON '{json_filepath}' tidak ditemukan.")
        return

    # 1. Baca file ASS asli
    with open(ass_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. Baca file JSON yang sudah diterjemahkan
    with open(json_filepath, 'r', encoding='utf-8') as f:
        translated_data = json.load(f)

    # 3. Masukkan teks yang sudah diterjemahkan ke baris yang sesuai
    injected_count = 0
    for item in translated_data:
        line_idx = item.get("line_index")
        translated_text = item.get("text")
        
        if line_idx is not None and line_idx < len(lines):
            original_line = lines[line_idx]
            if original_line.startswith("Dialogue:"):
                # Split ASS format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
                parts = original_line.strip().split(',', 9)
                if len(parts) == 10 and translated_text is not None:
                    # Ganti teks asli (index 9) dengan teks terjemahan
                    parts[9] = str(translated_text)
                    # Gabungkan kembali menjadi satu baris utuh
                    lines[line_idx] = ",".join(parts) + "\n"
                    injected_count += 1

    # 4. Simpan ke file ASS output baru
    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
    print(f"Berhasil meng-inject {injected_count} baris ke file output: {output_filepath}")

if __name__ == "__main__":
    ass_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a.ass"
    json_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\subtitle_raw.json"
    output_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a_translated.ass"
    
    inject_json_to_ass(ass_file, json_file, output_file)
