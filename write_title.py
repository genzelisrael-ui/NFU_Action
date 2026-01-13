#!/usr/bin/env python3
"""
Write episode title from environment variable to file
This avoids ALL bash quoting issues
"""
import os
import sys

title = os.environ.get('EPISODE_TITLE', '')
if not title:
    print("ERROR: EPISODE_TITLE environment variable is not set", file=sys.stderr)
    sys.exit(1)

try:
    with open('/tmp/episode_title.txt', 'wb') as f:
        f.write(title.encode('utf-8'))
    print(f"✅ Wrote title to /tmp/episode_title.txt ({len(title)} chars)")
except Exception as e:
    print(f"ERROR writing title: {e}", file=sys.stderr)
    sys.exit(1)
