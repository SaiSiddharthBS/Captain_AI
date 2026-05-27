import os
import sys
# Add parent dir to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yt_dlp
from src.config import MEDIA_DIR

def download_song():
    print("--- Captain AI Music Downloader ---")
    
    # 1. Get Query
    query = input("Enter song name/search query: ").strip()
    if not query: return
    
    # 2. Get Category
    print("\nFolders:")
    
    # Ensure folders exist
    default_folders = ["Chill", "Devotional", "Workout", "Favorites"]
    for f in default_folders:
        os.makedirs(os.path.join(MEDIA_DIR, f), exist_ok=True)
        
    categories = [d for d in os.listdir(MEDIA_DIR) if os.path.isdir(os.path.join(MEDIA_DIR, d))]
    for i, cat in enumerate(categories):
        print(f"{i+1}. {cat}")
    
    cat_idx = input("Select folder number: ")
    try:
        category = categories[int(cat_idx)-1]
    except:
        print("Invalid selection.")
        return

    target_path = os.path.join(MEDIA_DIR, category)
    
    # 3. Download Options
    
    # Path to local ffmpeg
    bin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin')
    ffmpeg_exe = os.path.join(bin_dir, 'ffmpeg.exe')

    # 403 Fix: Use Android client and specific headers
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(target_path, '%(title)s.%(ext)s'),
        'ffmpeg_location': bin_dir, # Point to local ffmpeg
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False,
        # Bypass 403
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    print(f"\nSearching and Downloading to '{category}'...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Check if input is a URL or a search query
            if query.startswith("http"):
                 print("Source: Direct URL")
                 ydl.download([query])
            else:
                 print("Source: Search Query")
                 ydl.download([f"ytsearch:{query}"])
                 
        print("\n✅ Download Complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Note: You might need FFMPEG installed for MP3 conversion.")
        print("If it fails, try installing ffmpeg or checking internet.")

if __name__ == "__main__":
    download_song()
