"""
Membagi file menjadi beberapa folder.
"""

import os
import shutil
import math

def split_files_into_folders():
    # Input path folder sumber
    source_dir = rf"C:\Users\Nasrul Wahabi\Downloads\Documents\status"
    
    if not os.path.isdir(source_dir):
        print("Error: Folder tidak ditemukan.")
        return

    # Ambil semua file (abaikan folder jika ada di dalamnya)
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    total_files = len(files)
    
    if total_files == 0:
        print("Tidak ada file untuk dipindahkan.")
        return

    print(f"Ditemukan {total_files} file.")

    # Input jumlah part/bagian
    try:
        num_parts = int(input("Mau dibagi menjadi berapa part? "))
        if num_parts <= 0:
            raise ValueError
    except ValueError:
        print("Masukkan angka bulat yang valid dan lebih dari 0.")
        return

    # Hitung ukuran tiap folder
    # Menggunakan ceiling agar semua file tercover (file sisa akan masuk ke folder terakhir)
    size_per_folder = math.ceil(total_files / num_parts)

    for i in range(num_parts):
        # Buat nama folder (1, 2, 3, ...)
        folder_name = str(i + 1)
        target_path = os.path.join(source_dir, folder_name)
        
        # Buat folder jika belum ada
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        # Ambil slice file untuk part ini
        start_idx = i * size_per_folder
        end_idx = start_idx + size_per_folder
        batch = files[start_idx:end_idx]

        # Pindahkan file
        for file_name in batch:
            old_path = os.path.join(source_dir, file_name)
            new_path = os.path.join(target_path, file_name)
            shutil.move(old_path, new_path)

        print(f"Folder {folder_name} selesai: {len(batch)} file dipindahkan.")

    print("\nSelesai! File telah terbagi rata.")

if __name__ == "__main__":
    split_files_into_folders()