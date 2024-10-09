# main.py
from main import all_video_urls, all_audio_urls

import subprocess
import os

def download_and_merge(video_url, audio_url, output_file):
    try:
        print(f"Downloading and merging video: {video_url} and audio: {audio_url}...")
        command = [
            'ffmpeg', 
            '-i', video_url, 
            '-i', audio_url, 
            '-c:v', 'copy',  # Copy video without re-encoding
            '-c:a', 'aac',   # Re-encode audio to AAC
            '-strict', 'experimental',  # Allow AAC encoding
            output_file
        ]
        subprocess.run(command, check=True)
        print(f"Video and audio combined into {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading and merging: {e}")

def process_urls(video_urls, audio_urls):
    for i in range(len(video_urls)):
        final_output = f'final_output_{i + 1}.mp4'  # Unique final output filename

        # Download and merge video and audio in one go
        download_and_merge(video_urls[i], audio_urls[i], final_output)

if __name__ == "__main__":
    # Assuming you already have these lists populated elsewhere in your code
    # Process the URLs directly from the lists
    process_urls(all_video_urls, all_audio_urls)

    print("Merging complete! Check the final output files.")

