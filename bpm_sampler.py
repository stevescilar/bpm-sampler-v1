import os
import shutil
import librosa
import tkinter as tk
from tkinter import filedialog

# -----------------------------
# BPM RANGES
# -----------------------------
SLOW_MAX = 90
MEDIUM_MAX = 120

# -----------------------------
# SELECT MUSIC FOLDER
# -----------------------------
root = tk.Tk()
root.withdraw()

music_folder = filedialog.askdirectory(title="Select Music Folder")

if not music_folder:
    print("No folder selected.")
    exit()

# -----------------------------
# CREATE OUTPUT FOLDERS
# -----------------------------
slow_folder = os.path.join(music_folder, "Slow")
medium_folder = os.path.join(music_folder, "Medium")
fast_folder = os.path.join(music_folder, "Fast")

os.makedirs(slow_folder, exist_ok=True)
os.makedirs(medium_folder, exist_ok=True)
os.makedirs(fast_folder, exist_ok=True)

# -----------------------------
# PROCESS FILES
# -----------------------------
supported_formats = (".mp3", ".wav", ".flac", ".ogg")

for filename in os.listdir(music_folder):
    if not filename.lower().endswith(supported_formats):
        continue

    file_path = os.path.join(music_folder, filename)

    try:
        # Load audio
        y, sr = librosa.load(file_path, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(round(tempo.item()))
        # bpm = round(float(tempo))

        # Decide folder
        if bpm < SLOW_MAX:
            target = slow_folder
        elif bpm <= MEDIUM_MAX:
            target = medium_folder
        else:
            target = fast_folder

        shutil.move(file_path, os.path.join(target, filename))

        print(f"{filename} → {bpm} BPM → {os.path.basename(target)}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

print("\n✅ Sorting completed!")
