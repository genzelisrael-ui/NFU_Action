#!/usr/bin/env python3
"""Write episodes JSON from environment variable to file with UTF-8 encoding."""
import os
import sys

def main():
    # קרא את ה-JSON מה-environment variable
    episodes_json = os.environ.get('EPISODES_JSON', '')
    
    if not episodes_json:
        print("Error: EPISODES_JSON environment variable is empty", file=sys.stderr)
        sys.exit(1)
    
    # כתוב לקובץ עם UTF-8 encoding
    output_file = '/tmp/episodes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(episodes_json)
    
    print(f"Wrote {len(episodes_json)} characters to {output_file}")
    
    # הצג דוגמה של התוכן
    print(f"First 200 chars: {episodes_json[:200]}")

if __name__ == '__main__':
    main()
