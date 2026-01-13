#!/usr/bin/env python3
"""Read episode title from file and generate safe filename."""
import sys

def safe_filename(title):
    """Clean title for use as filename, preserving Hebrew characters."""
    if not title:
        return None
    
    # Remove/replace only truly problematic characters for filesystems
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '#': ''
    }
    
    for old, new in replacements.items():
        title = title.replace(old, new)
    
    # Normalize whitespace
    title = ' '.join(title.split())
    
    return title + '.mp3'

if __name__ == '__main__':
    # Read from file
    title_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/episode_title.txt'
    
    try:
        with open(title_file, 'r', encoding='utf-8') as f:
            title = f.read().strip()
        
        if title:
            filename = safe_filename(title)
            if filename:
                print(filename)
            else:
                print(f"episode_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
        else:
            print(f"episode_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
    except FileNotFoundError:
        print(f"episode_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
