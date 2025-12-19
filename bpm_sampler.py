import os
import shutil
import librosa
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
from datetime import datetime
import csv
import threading
import hashlib


class MusicBPMSorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music BPM Sorter")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Variables
        self.music_folder = None
        self.is_processing = False
        self.results = []

        # BPM Range Variables
        self.slow_max = tk.IntVar(value=90)
        self.medium_max = tk.IntVar(value=120)

        # Duplicate removal option
        self.remove_duplicates = tk.BooleanVar(value=False)
        self.duplicates_found = []

        # Create GUI
        self.create_widgets()

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="🎵 Music BPM Sorter", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Folder Selection
        ttk.Label(main_frame, text="Music Folder:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.folder_label = ttk.Label(
            main_frame, text="No folder selected", relief=tk.SUNKEN, width=50
        )
        self.folder_label.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.browse_btn = ttk.Button(
            main_frame, text="Browse", command=self.browse_folder
        )
        self.browse_btn.grid(row=1, column=2, padx=5, pady=5)

        # BPM Range Settings
        settings_frame = ttk.LabelFrame(
            main_frame, text="BPM Range Settings", padding="10"
        )
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Slow (≤):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        slow_spin = ttk.Spinbox(
            settings_frame, from_=60, to=100, textvariable=self.slow_max, width=10
        )
        slow_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="BPM").grid(row=0, column=2, sticky=tk.W, pady=5)

        ttk.Label(settings_frame, text="Medium (≤):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        medium_spin = ttk.Spinbox(
            settings_frame, from_=90, to=150, textvariable=self.medium_max, width=10
        )
        medium_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="BPM").grid(row=1, column=2, sticky=tk.W, pady=5)

        ttk.Label(settings_frame, text="Fast (>):").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.fast_label = ttk.Label(settings_frame, text=f"{self.medium_max.get()} BPM")
        self.fast_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Update fast label when medium changes
        self.medium_max.trace_add("write", self.update_fast_label)

        # Duplicate Removal Option
        duplicate_frame = ttk.LabelFrame(
            main_frame, text="Duplicate Detection", padding="10"
        )
        duplicate_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )

        self.dup_check = ttk.Checkbutton(
            duplicate_frame,
            text="Remove duplicate files (keeps first occurrence)",
            variable=self.remove_duplicates,
        )
        self.dup_check.grid(row=0, column=0, sticky=tk.W, pady=5)

        dup_info = ttk.Label(
            duplicate_frame,
            text="Detects duplicates by comparing file content (hash)",
            font=("Arial", 8),
            foreground="gray",
        )
        dup_info.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(
            button_frame,
            text="Start Sorting",
            command=self.start_sorting,
            state=tk.DISABLED,
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = ttk.Button(
            button_frame,
            text="Export Results",
            command=self.export_results,
            state=tk.DISABLED,
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Log Text Area
        log_frame = ttk.LabelFrame(main_frame, text="Processing Log", padding="5")
        log_frame.grid(
            row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, width=80, state=tk.DISABLED, wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status Bar
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(
            row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0)
        )

    def update_fast_label(self, *args):
        self.fast_label.config(text=f"{self.medium_max.get()} BPM")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            self.music_folder = folder
            self.folder_label.config(text=folder)
            self.start_btn.config(state=tk.NORMAL)
            self.log("Folder selected: " + folder)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, message):
        self.status_label.config(text=message)

    def calculate_file_hash(self, filepath, chunk_size=8192):
        """Calculate MD5 hash of file for duplicate detection"""
        hasher = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.log(f"  ⚠️ Hash error: {str(e)}")
            return None

    def find_duplicates(self, audio_files):
        """Find duplicate files based on content hash"""
        self.log("\n🔍 Scanning for duplicates...")
        file_hashes = {}
        duplicates = []

        for i, filename in enumerate(audio_files, 1):
            file_path = os.path.join(self.music_folder, filename)
            self.update_status(f"Checking duplicates {i}/{len(audio_files)}")
            self.root.after(0, lambda val=i: self.progress.config(value=val))

            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                if file_hash in file_hashes:
                    duplicates.append(
                        {
                            "original": file_hashes[file_hash],
                            "duplicate": filename,
                            "hash": file_hash,
                        }
                    )
                    self.log(
                        f"  🔄 Duplicate found: {filename} (matches {file_hashes[file_hash]})"
                    )
                else:
                    file_hashes[file_hash] = filename

        return duplicates, file_hashes

    def remove_duplicate_files(self, duplicates):
        """Move duplicate files to a Duplicates folder"""
        if not duplicates:
            return

        duplicates_folder = os.path.join(self.music_folder, "Duplicates")
        os.makedirs(duplicates_folder, exist_ok=True)

        self.log(f"\n🗑️ Moving {len(duplicates)} duplicate(s) to 'Duplicates' folder...")

        for dup in duplicates:
            try:
                src = os.path.join(self.music_folder, dup["duplicate"])
                dst = os.path.join(duplicates_folder, dup["duplicate"])

                # Handle filename conflicts in duplicates folder
                if os.path.exists(dst):
                    name, ext = os.path.splitext(dup["duplicate"])
                    counter = 1
                    while os.path.exists(dst):
                        dst = os.path.join(duplicates_folder, f"{name}_{counter}{ext}")
                        counter += 1

                shutil.move(src, dst)
                self.log(f"  ✓ Moved: {dup['duplicate']}")
            except Exception as e:
                self.log(f"  ✗ Error moving {dup['duplicate']}: {str(e)}")

    def start_sorting(self):
        if not self.music_folder:
            self.log("❌ No folder selected!")
            return

        if self.is_processing:
            return

        # Clear previous results
        self.results = []
        self.duplicates_found = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Disable buttons
        self.start_btn.config(state=tk.DISABLED)
        self.browse_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)

        # Start processing in thread
        self.is_processing = True
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def process_files(self):
        try:
            # Create output folders
            slow_folder = os.path.join(self.music_folder, "Slow")
            medium_folder = os.path.join(self.music_folder, "Medium")
            fast_folder = os.path.join(self.music_folder, "Fast")

            os.makedirs(slow_folder, exist_ok=True)
            os.makedirs(medium_folder, exist_ok=True)
            os.makedirs(fast_folder, exist_ok=True)

            self.log("📁 Created sorting folders\n")

            # Get audio files
            supported_formats = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")
            audio_files = [
                f
                for f in os.listdir(self.music_folder)
                if f.lower().endswith(supported_formats)
                and os.path.isfile(os.path.join(self.music_folder, f))
            ]

            total_files = len(audio_files)

            if total_files == 0:
                self.log("❌ No audio files found!")
                self.is_processing = False
                self.root.after(0, self.enable_buttons)
                return

            # Handle duplicates if option is enabled
            files_to_process = audio_files
            if self.remove_duplicates.get():
                self.progress["maximum"] = total_files
                duplicates, file_hashes = self.find_duplicates(audio_files)
                self.duplicates_found = duplicates

                if duplicates:
                    self.remove_duplicate_files(duplicates)
                    # Update list to exclude duplicates
                    duplicate_names = {d["duplicate"] for d in duplicates}
                    files_to_process = [
                        f for f in audio_files if f not in duplicate_names
                    ]
                    self.log(f"\n✅ Removed {len(duplicates)} duplicate(s)")
                    self.log(f"📝 Processing {len(files_to_process)} unique files\n")
                else:
                    self.log("✅ No duplicates found\n")

            total_files = len(files_to_process)
            if total_files == 0:
                self.log("❌ No files left to process after duplicate removal!")
                self.is_processing = False
                self.root.after(0, self.enable_buttons)
                return

            self.log(f"Found {total_files} audio files to process\n")
            self.progress["maximum"] = total_files

            # Process each file
            for i, filename in enumerate(files_to_process, 1):
                file_path = os.path.join(self.music_folder, filename)

                try:
                    self.log(f"[{i}/{total_files}] {filename}")
                    self.update_status(f"Processing {i}/{total_files}: {filename}")

                    # Load and analyze
                    y, sr = librosa.load(file_path, mono=True)
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                    bpm = int(round(tempo.item()))

                    # Adjust for detection errors
                    if bpm < 60:
                        bpm *= 2
                    elif bpm > 200:
                        bpm //= 2

                    # Categorize
                    slow_max = self.slow_max.get()
                    medium_max = self.medium_max.get()

                    if bpm <= slow_max:
                        target = slow_folder
                        category = "Slow"
                    elif bpm <= medium_max:
                        target = medium_folder
                        category = "Medium"
                    else:
                        target = fast_folder
                        category = "Fast"

                    # Move file
                    shutil.move(file_path, os.path.join(target, filename))

                    # Store result
                    self.results.append(
                        {"filename": filename, "bpm": bpm, "category": category}
                    )

                    self.log(f"  ✓ {bpm} BPM → {category}\n")

                except Exception as e:
                    self.log(f"  ✗ Error: {str(e)}\n")
                    self.results.append(
                        {"filename": filename, "bpm": "Error", "category": "Not Sorted"}
                    )

                # Update progress
                self.root.after(0, lambda val=i: self.progress.config(value=val))

            # Show summary
            self.show_summary()

        finally:
            self.is_processing = False
            self.root.after(0, self.enable_buttons)

    def show_summary(self):
        self.log("\n" + "=" * 50)
        self.log("📊 SORTING SUMMARY")
        self.log("=" * 50)

        # Duplicate summary
        if self.remove_duplicates.get() and self.duplicates_found:
            self.log(f"Duplicates removed:  {len(self.duplicates_found)} files")
            self.log("-" * 50)

        slow_count = len([r for r in self.results if r["category"] == "Slow"])
        medium_count = len([r for r in self.results if r["category"] == "Medium"])
        fast_count = len([r for r in self.results if r["category"] == "Fast"])
        error_count = len([r for r in self.results if r["category"] == "Not Sorted"])

        self.log(f"Slow (≤{self.slow_max.get()} BPM):     {slow_count} tracks")
        self.log(
            f"Medium ({self.slow_max.get()+1}-{self.medium_max.get()} BPM): {medium_count} tracks"
        )
        self.log(f"Fast (>{self.medium_max.get()} BPM):      {fast_count} tracks")
        if error_count > 0:
            self.log(f"Errors:              {error_count} tracks")
        self.log("=" * 50)
        self.log("\n✅ Sorting completed!")

        self.update_status("Sorting completed!")

    def enable_buttons(self):
        self.start_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)
        if self.results:
            self.export_btn.config(state=tk.NORMAL)

    def export_results(self):
        if not self.results and not self.duplicates_found:
            self.log("❌ No results to export!")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"bpm_analysis_{timestamp}.csv"
        csv_path = os.path.join(self.music_folder, csv_filename)

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Song Title", "BPM", "Category", "Notes"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                # Write duplicate info if any
                if self.duplicates_found:
                    writer.writerow(
                        {
                            "Song Title": "--- DUPLICATES REMOVED ---",
                            "BPM": "",
                            "Category": "",
                            "Notes": "",
                        }
                    )
                    for dup in self.duplicates_found:
                        writer.writerow(
                            {
                                "Song Title": dup["duplicate"],
                                "BPM": "N/A",
                                "Category": "Duplicate",
                                "Notes": f"Duplicate of: {dup['original']}",
                            }
                        )
                    writer.writerow(
                        {"Song Title": "", "BPM": "", "Category": "", "Notes": ""}
                    )
                    writer.writerow(
                        {
                            "Song Title": "--- SORTED FILES ---",
                            "BPM": "",
                            "Category": "",
                            "Notes": "",
                        }
                    )

                # Write sorted files
                for result in self.results:
                    writer.writerow(
                        {
                            "Song Title": result["filename"],
                            "BPM": result["bpm"],
                            "Category": result["category"],
                            "Notes": "",
                        }
                    )

            self.log(f"\n✅ Results exported to: {csv_filename}")
            self.update_status(f"Exported: {csv_filename}")

        except Exception as e:
            self.log(f"\n❌ Export failed: {str(e)}")
            self.update_status("Export failed")


def main():
    root = tk.Tk()
    app = MusicBPMSorterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
