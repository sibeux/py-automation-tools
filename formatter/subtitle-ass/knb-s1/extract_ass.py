"""
Script for extracting dialog text only from ass subtitle files.
"""

import json
import os

def extract_ass_to_json(ass_filepath, json_filepath):
    if not os.path.exists(ass_filepath):
        print(f"Error: File {ass_filepath} tidak ditemukan.")
        return

    with open(ass_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    json_data = []
    
    for i, line in enumerate(lines):
        if line.startswith("Dialogue:"):
            # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            # Kita split berdasarkan koma maksimal 9 kali agar teks yang mengandung koma tidak terpisah
            parts = line.strip().split(',', 9)
            if len(parts) == 10:
                style = parts[3]
                text = parts[9]
                
                # Gunakan "Smart Whitelist" agar universal TAPI tetap bersih
                style_lower = style.lower()
                
                # 1. Style HARUS mengandung salah satu kata kunci dialog ini:
                allowed_keywords = ["main", "dialogue", "default", "thought", "narrator", "flashback", "overlap", "top", "title"]
                is_dialogue = any(kw in style_lower for kw in allowed_keywords)
                
                # 2. Pastikan bukan lagu (jaga-jaga kalau namanya "OP Dialogue")
                forbidden_keywords = ["op ", "ed ", "karaoke", "romaji", "kanji", "song"]
                is_forbidden = any(kw in style_lower for kw in forbidden_keywords)
                
                # 3. Abaikan kode gambar vektor
                import re
                is_vector_drawing = bool(re.search(r'\\p\d+', text))
                
                if is_dialogue and not is_forbidden and not is_vector_drawing:
                    json_data.append({
                        "line_index": i,
                        "start": parts[1],
                        "end": parts[2],
                        "style": style,
                        "text": text
                    })

    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
        
    print(f"Berhasil mengekstrak {len(json_data)} baris dialog ke {json_filepath}")
    print("Silakan gunakan file JSON ini ke AI untuk menerjemahkan value 'text'.")

if __name__ == "__main__":
    ass_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a.ass"  # Ganti dengan nama file ass Anda jika berbeda
    json_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\subtitle_raw.json"
    
    extract_ass_to_json(ass_file, json_file)
