#!/usr/bin/env python3
"""Download multiple episodes with automatic podcast folder creation and metadata."""
import json
import subprocess
import os
import sys
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC
import requests

def sanitize_folder_name(name):
    """Clean podcast name for folder creation."""
    # Remove invalid chars for folders
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()

def add_metadata_to_mp3(file_path, episode_data, podcast_data):
    """Add ID3 metadata to MP3 file."""
    try:
        audio = MP3(file_path, ID3=ID3)
        
        # Add ID3 tag if doesn't exist
        try:
            audio.add_tags()
        except:
            pass
        
        # Episode title
        audio.tags.add(TIT2(encoding=3, text=episode_data.get('title', '')))
        
        # Podcast title as album
        audio.tags.add(TALB(encoding=3, text=podcast_data.get('title', '')))
        
        # Artist/Author
        if 'author' in podcast_data:
            audio.tags.add(TPE1(encoding=3, text=podcast_data['author']))
        
        # Year
        if 'pub_date' in episode_data:
            year = episode_data['pub_date'][:4]  # Extract year from date
            audio.tags.add(TDRC(encoding=3, text=year))
        
        # Genre
        audio.tags.add(TCON(encoding=3, text='Podcast'))
        
        # Cover art
        if 'cover_url' in podcast_data:
            try:
                response = requests.get(podcast_data['cover_url'], timeout=10)
                if response.status_code == 200:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,  # Cover image
                            desc='Cover',
                            data=response.content
                        )
                    )
            except Exception as e:
                print(f"  Warning: Could not download cover art: {e}")
        
        audio.save()
        print(f"  ✓ Metadata added")
    except Exception as e:
        print(f"  Warning: Could not add metadata: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: download_multiple_episodes.py <episodes_json_file> <base_folder>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    base_folder = sys.argv[2]
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract podcast info and episodes
    if isinstance(data, dict) and 'episodes' in data:
        podcast_data = {
            'title': data.get('podcast_title', 'Unknown Podcast'),
            'author': data.get('author'),
            'cover_url': data.get('cover_url')
        }
        episodes = data['episodes']
    else:
        # Legacy format - just episodes array
        podcast_data = {'title': 'Podcast'}
        episodes = data
    
    # Create podcast folder
    podcast_folder_name = sanitize_folder_name(podcast_data['title'])
    podcast_folder = os.path.join(base_folder, podcast_folder_name)
    os.makedirs(podcast_folder, exist_ok=True)
    print(f"📁 Created podcast folder: {podcast_folder}")
    
    print(f"Found {len(episodes)} episodes to download")
    
    for i, episode in enumerate(episodes, 1):
        url = episode.get('url')
        title = episode.get('title')
        
        if not url or not title:
            print(f"Skipping episode {i}: missing url or title")
            continue
        
        print(f"\n=== Downloading episode {i}/{len(episodes)}: {title} ===")
        
        # Generate filename
        with open('/tmp/episode_title.txt', 'w', encoding='utf-8') as f:
            f.write(title)
        
        result = subprocess.run(['python3', 'generate_filename_from_file.py', '/tmp/episode_title.txt'],
                              capture_output=True, text=True, encoding='utf-8')
        filename = result.stdout.strip()
        
        if not filename:
            filename = f"episode_{i}.mp3"
        
        print(f"Downloading to: {filename}")
        
        # Download to podcast folder
        target_path = os.path.join(podcast_folder, filename)
        wget_cmd = ['wget', '-O', target_path, url]
        
        try:
            subprocess.run(wget_cmd, check=True)
            print(f"  ✓ Downloaded successfully")
            
            # Add metadata
            add_metadata_to_mp3(target_path, episode, podcast_data)
            
        except subprocess.CalledProcessError:
            print(f"  wget failed, trying curl...")
            curl_cmd = ['curl', '-L', '-o', target_path, url]
            try:
                subprocess.run(curl_cmd, check=True)
                print(f"  ✓ Downloaded successfully with curl")
                
                # Add metadata
                add_metadata_to_mp3(target_path, episode, podcast_data)
                
            except subprocess.CalledProcessError:
                print(f"  ✗ Failed to download episode {i}")
    
    print(f"\n=== All downloads completed in: {podcast_folder} ===")

if __name__ == '__main__':
    main()

