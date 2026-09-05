"""
Script for extracting dialogue, episode title, and song translations from ASS subtitle files.
Outputs JSON format compatible with subtitle translation workflows.
"""

import json
import os
import re

def extract_ass_to_json(ass_filepath, json_filepath, include_songs=True):
    if not os.path.exists(ass_filepath):
        print(f"Error: File {ass_filepath} tidak ditemukan.")
        return

    with open(ass_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    json_data = []
    
    for i, line in enumerate(lines):
        if line.startswith("Dialogue:"):
            # Format ASS: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            parts = line.strip().split(',', 9)
            if len(parts) == 10:
                style = parts[3]
                text = parts[9]
                style_lower = style.lower()
                
                # 1. Kata kunci style dialog & judul
                dialogue_keywords = [
                    "main", "dialogue", "default", "thought", "narrator", 
                    "flashback", "overlap", "top", "title", "eptitle"
                ]
                is_dialogue = any(kw in style_lower for kw in dialogue_keywords)
                
                # 2. Baris terjemahan lagu (seperti oprom-eng-top, optrans, edtrans)
                is_song_translation = False
                if include_songs:
                    song_trans_keywords = ["-eng-", "trans"]
                    is_song_translation = any(sk in style_lower for sk in song_trans_keywords)
                
                # 3. Filter efek romaji, kanji, logo, dan typesetting murni
                forbidden_keywords = ["romaji", "kanji", "karaoke", "logo", "sign", "mask", "scoreboard", "onscreen"]
                is_forbidden = any(kw in style_lower for kw in forbidden_keywords) and not is_song_translation
                
                # 4. Abaikan kode gambar vektor ASS (\\p1, \\p2, dst)
                is_vector_drawing = bool(re.search(r'\\p\d+', text))
                
                # 5. Abaikan baris kosong
                if not text.strip():
                    continue

                if (is_dialogue or is_song_translation) and not is_forbidden and not is_vector_drawing:
                    json_data.append({
                        "line_index": i,
                        "start": parts[1],
                        "end": parts[2],
                        "style": style,
                        "text": text
                    })

    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
        
    print(f"Berhasil mengekstrak {len(json_data)} baris ke {json_filepath}")
    print("Silakan gunakan file JSON ini ke AI untuk menerjemahkan value 'text'.")

if __name__ == "__main__":
    ass_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\a.ass"
    json_file = rf"C:\Users\Nasrul Wahabi\Downloads\Telegram Desktop\subtitle_raw.json"
    
    extract_ass_to_json(ass_file, json_file, include_songs=True)
