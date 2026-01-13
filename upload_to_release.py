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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def upload_single_file(session, upload_url_base, token, file_path, index):
    """Upload a single file used by ThreadPoolExecutor."""
    try:
        file_path = Path(file_path)
        filename = file_path.name
        
        # URL encode the filename for GitHub API
        encoded_filename = quote(filename, safe='')
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Upload headers
        upload_headers = {
            'Authorization': f'token {token}',
            'Content-Type': content_type
        }
        
        upload_url_with_name = f'{upload_url_base}?name={encoded_filename}'
        
        print(f'>> Starting upload: {filename}')
        
        with open(file_path, 'rb') as f:
            response = session.post(
                upload_url_with_name,
                headers=upload_headers,
                data=f,
                timeout=300 # 5 minutes timeout per file
            )
        
        if response.status_code in (200, 201):
            result = response.json()
            asset_id = result.get('id')
            print(f'++ Finished upload: {filename}')
            return (True, filename, asset_id, index)
        else:
            print(f'!! Failed to upload {filename}: {response.status_code} - {response.text}')
            return (False, filename, None, index)
            
    except Exception as e:
        print(f'!! Exception during upload of {file_path}: {str(e)}')
        return (False, str(file_path), None, index)

def upload_to_release_parallel(token, owner, repo, tag_name, file_paths):
    """Upload files to a GitHub release in parallel.    
    Returns list of results.
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
            print(f'!! Failed to get release: {response.status_code} - {response.text}')
            return []
        
        release = response.json()
        upload_url_base = release['upload_url'].split('{')[0]
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {
                executor.submit(upload_single_file, session, upload_url_base, token, fp, idx): idx 
                for idx, fp in enumerate(file_paths)
            }
            
            for future in as_completed(future_to_file):
                idx = future_to_file[future]
                try:
                    success, name, asset_id, original_idx = future.result()
                    if success:
                        results.append({
                            'index': original_idx,
                            'original_name': name,
                            'asset_id': asset_id
                        })
                except Exception as exc:
                    print(f'!! Generated an exception for file index {idx}: {exc}')
                    
        return results

    except Exception as e:
        print(f'!! Global error during upload process: {str(e)}')
        return []

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: python upload_to_release.py <token> <owner> <repo> <tag_name> <file_path> [file_path...]')
        sys.exit(1)
    
    token = sys.argv[1]
    owner = sys.argv[2]
    repo = sys.argv[3]
    tag_name = sys.argv[4]
    file_paths = sys.argv[5:]
    
    # Filter only existing files
    valid_paths = []
    for fp in file_paths:
        if os.path.exists(fp):
            valid_paths.append(fp)
        else:
             print(f'** File not found (skipping): {fp}')

    print(f'>> Starting parallel upload for {len(valid_paths)} files...')
    
    filename_mapping = upload_to_release_parallel(token, owner, repo, tag_name, valid_paths)
    
    success_count = len(filename_mapping)
    print(f'\n== Results: {success_count} succeeded out of {len(valid_paths)} attempts')
    
    # Output JSON mapping for server to parse
    if filename_mapping:
        print('\n===FILENAME_MAPPING_START===')
        import base64
        # Sort by index to maintain original order if needed, though mostly relevant for mapping
        filename_mapping.sort(key=lambda x: x['index'])
        json_str = json.dumps(filename_mapping, ensure_ascii=True)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
        print(encoded)
        print('===FILENAME_MAPPING_END===')
    
    sys.exit(0 if success_count == len(valid_paths) else 1)
