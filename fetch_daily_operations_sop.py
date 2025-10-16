#!/usr/bin/env python3
"""
Fetch "Daily Operations: How to Label & Reconcile" from Confluence
This page contains the actual labeling rules!
"""
import os
from dotenv import load_dotenv
from atlassian import Confluence
import json
import re

load_dotenv()

confluence = Confluence(
    url=os.environ.get("CONFLUENCE_URL", "https://gustohq.atlassian.net"),
    username=os.environ.get("CONFLUENCE_USERNAME"),
    password=os.environ.get("CONFLUENCE_API_TOKEN"),
    cloud=True
)

def search_for_page(title):
    """Search for a page by title."""
    try:
        print(f"Searching for: {title}")
        results = confluence.cql(
            f'space="PlatformOperations" AND type=page AND title~"{title}"',
            limit=5
        )
        
        if results and 'results' in results:
            for result in results['results']:
                content = result.get('content', {})
                page_id = content.get('id')
                page_title = content.get('title')
                print(f"  Found: {page_title} (ID: {page_id})")
                return page_id
        
        return None
    except Exception as e:
        print(f"Error searching: {e}")
        return None

def fetch_page_content(page_id):
    """Fetch page content."""
    try:
        page = confluence.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version'
        )
        
        if page:
            return {
                'title': page.get('title'),
                'id': page_id,
                'content': page.get('body', {}).get('storage', {}).get('value', ''),
                'url': f"https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/{page_id}"
            }
        return None
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_text_from_html(html_content):
    """Extract plain text from HTML."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '\n', html_content)
    # Decode HTML entities
    import html
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def main():
    print("\n" + "="*80)
    print("FETCHING 'DAILY OPERATIONS: HOW TO LABEL & RECONCILE'")
    print("="*80 + "\n")
    
    # Search for the page
    page_id = search_for_page("Daily Operations How to Label Reconcile")
    
    if not page_id:
        print("❌ Page not found. Trying alternative search...")
        page_id = search_for_page("Daily Operations")
    
    if page_id:
        print(f"\n✅ Found page ID: {page_id}")
        print("Fetching content...\n")
        
        content = fetch_page_content(page_id)
        
        if content:
            # Save raw HTML
            filename = f"confluence_daily_operations_{page_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved HTML to: {filename}")
            
            # Extract and save plain text
            plain_text = extract_text_from_html(content['content'])
            text_filename = f"confluence_daily_operations_{page_id}.txt"
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(f"Title: {content['title']}\n")
                f.write(f"URL: {content['url']}\n")
                f.write("="*80 + "\n\n")
                f.write(plain_text)
            print(f"✅ Saved plain text to: {text_filename}")
            
            # Show preview
            print("\n" + "="*80)
            print("PREVIEW (first 2000 characters):")
            print("="*80)
            print(plain_text[:2000])
            print("\n... (see full text in .txt file)")
            
        else:
            print("❌ Failed to fetch page content")
    else:
        print("❌ Could not find the page")
        print("\nTrying to list all pages in PlatformOperations space...")
        
        try:
            results = confluence.cql(
                'space="PlatformOperations" AND type=page AND title~"Daily"',
                limit=20
            )
            
            print("\nPages found with 'Daily' in title:")
            for result in results.get('results', []):
                content = result.get('content', {})
                print(f"  • {content.get('title')} (ID: {content.get('id')})")
        except Exception as e:
            print(f"Error listing pages: {e}")

if __name__ == "__main__":
    main()

