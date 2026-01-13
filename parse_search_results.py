#!/usr/bin/env python3
"""Parse YouTube search results from yt-dlp JSON output."""
import json
import sys

results = []
try:
    with open('/tmp/search_results.json', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    video = json.loads(line)
                    video_id = video.get('id')
                    # Generate thumbnail URL from video ID (YouTube standard format)
                    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
                    
                    results.append({
                        'id': video_id,
                        'title': video.get('title'),
                        'channel': video.get('channel') or video.get('uploader'),
                        'duration': video.get('duration'),
                        'view_count': video.get('view_count'),
                        'thumbnail': thumbnail_url,
                        'url': f"https://youtube.com/watch?v={video_id}"
                    })
                except json.JSONDecodeError:
                    pass
except FileNotFoundError:
    print("No results found")
    sys.exit(1)

# Output results as JSON
output = {
    'ok': True,
    'query': sys.argv[1] if len(sys.argv) > 1 else '',
    'count': len(results),
    'results': results
}

print('===SEARCH_RESULTS_START===')
print(json.dumps(output, ensure_ascii=False, indent=2))
print('===SEARCH_RESULTS_END===')

# Save to file for artifact
with open('search_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Found {len(results)} videos")
