#!/usr/bin/env python3
"""Clean MP3 filenames for GitHub upload while preserving Hebrew characters."""
import os
import re
import glob
import sys

def clean_filename(filename):
    """Remove problematic characters but preserve Hebrew."""
    # Only replace: # < > : " | ? * and normalize spaces
    clean = filename.replace('#', '').replace('<', '_').replace('>', '_')
    clean = clean.replace(':', '_').replace('"', '_').replace('|', '_')
    clean = clean.replace('?', '_').replace('*', '_')
    # Normalize multiple spaces to single space
    clean = re.sub(r'\s+', ' ', clean)
    return clean

def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.chdir(folder)
    
    for mp3_file in glob.glob('**/*.mp3', recursive=True):
        dir_name = os.path.dirname(mp3_file)
        filename = os.path.basename(mp3_file)
        
        clean = clean_filename(filename)
        
        if filename != clean:
            old_path = os.path.join(dir_name, filename)
            new_path = os.path.join(dir_name, clean)
            print(f'Renaming: {filename} -> {clean}')
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(f'Failed to rename: {filename} - {e}')
        else:
            print(f'No change needed: {filename}')

if __name__ == '__main__':
    main()
