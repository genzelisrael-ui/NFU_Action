#!/usr/bin/env python3
"""Upload files to GitHub Release with proper Hebrew filename support."""
import sys
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import mimetypes
import json
from pathlib import Path
from urllib.parse import quote

def create_retry_session(retries=5, backoff_factor=1, status_forcelist=None):
    """Create a requests session with retry logic."""
    session = requests.Session()
    
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]
    
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def upload_to_release(token, owner, repo, tag_name, file_path):
    """Upload a file to a GitHub release with proper Unicode handling.
    
    Returns tuple: (success: bool, original_filename: str, asset_id: int)
    """
    # Create session with retries
    session = create_retry_session()

    # Get release by tag
    url = f'https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_name}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            print(f'\u274c Failed to get release: {response.status_code} - {response.text}')
            return (False, None, None)
        
        release = response.json()
        upload_url = release['upload_url'].split('{')[0]
        
        # Get filename and content type
        file_path = Path(file_path)
        filename = file_path.name
        
        # URL encode the filename for GitHub API
        encoded_filename = quote(filename, safe='')
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Upload file
        upload_headers = {
            'Authorization': f'token {token}',
            'Content-Type': content_type
        }
        
        upload_url_with_name = f'{upload_url}?name={encoded_filename}'
        
        with open(file_path, 'rb') as f:
            response = session.post(
                upload_url_with_name,
                headers=upload_headers,
                data=f
            )
        
        if response.status_code in (200, 201):
            result = response.json()
            asset_id = result.get('id')
            print(f'\u2705 Successfully uploaded: {filename}')
            return (True, filename, asset_id)
        else:
            print(f'\u274c Failed to upload {filename}: {response.status_code} - {response.text}')
            return (False, None, None)
            
    except requests.exceptions.RequestException as e:
        print(f'\u274c Exception during upload of {file_path}: {str(e)}')
        return (False, None, None)

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: python upload_to_release.py <token> <owner> <repo> <tag_name> <file_path> [file_path...]')
        sys.exit(1)
    
    token = sys.argv[1]
    owner = sys.argv[2]
    repo = sys.argv[3]
    tag_name = sys.argv[4]
    file_paths = sys.argv[5:]
    
    success_count = 0
    fail_count = 0
    filename_mapping = []
    
    for idx, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f'\u274c File not found: {file_path}')
            fail_count += 1
            continue
        
        success, original_name, asset_id = upload_to_release(token, owner, repo, tag_name, file_path)
        if success:
            success_count += 1
            filename_mapping.append({
                'index': idx,
                'original_name': original_name,
                'asset_id': asset_id
            })
        else:
            fail_count += 1
    
    print(f'\n\ud83d\udcca Results: {success_count} succeeded, {fail_count} failed')
    
    # Output JSON mapping for server to parse (Base64 encoded to avoid GitHub Actions log corruption)
    if filename_mapping:
        print('\n===FILENAME_MAPPING_START===')
        import base64
        json_str = json.dumps(filename_mapping, ensure_ascii=True)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        print(encoded)
        print('===FILENAME_MAPPING_END===')
    
    sys.exit(0 if fail_count == 0 else 1)
