#!/usr/bin/env python3
"""
Fetch specific SOP pages from Confluence
"""
import os
from dotenv import load_dotenv
from atlassian import Confluence
import json
import re
from bs4 import BeautifulSoup

load_dotenv()

confluence = Confluence(
    url=os.environ.get("CONFLUENCE_URL", "https://gustohq.atlassian.net"),
    username=os.environ.get("CONFLUENCE_USERNAME"),
    password=os.environ.get("CONFLUENCE_API_TOKEN"),
    cloud=True
)

# Key SOP Pages
SOP_PAGES = {
    "Manual Reconciliation Checks": "169412024",
    "Daily Operations How to Label & Reconcile": None,  # Will search for this
    "Labeling Bank Transactions": None,  # Will search for this
}

def fetch_page_by_id(page_id):
    """Fetch a specific page by ID."""
    try:
        print(f"Fetching page {page_id}...")
        page = confluence.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version'
        )
        
        if page:
            title = page.get('title')
            content = page.get('body', {}).get('storage', {}).get('value', '')
            print(f"✅ Found: {title}")
            print(f"   Content length: {len(content)} characters")
            
            return {
                'title': title,
                'id': page_id,
                'content': content,
                'url': f"https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/{page_id}"
            }
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def search_for_page(title_query):
    """Search for a page by title."""
    try:
        print(f"Searching for: {title_query}")
        results = confluence.cql(
            f'space="PlatformOperations" AND type=page AND title~"{title_query}"',
            limit=10
        )
        
        if results and 'results' in results:
            print(f"  Found {len(results['results'])} results:")
            for result in results['results']:
                content = result.get('content', {})
                page_id = content.get('id')
                page_title = content.get('title')
                print(f"    • {page_title} (ID: {page_id})")
            
            if results['results']:
                return results['results'][0].get('content', {}).get('id')
        
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_readable_text(html_content):
    """Extract readable text from HTML using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except:
        # Fallback to regex if BeautifulSoup fails
        text = re.sub(r'<[^>]+>', '\n', html_content)
        import html
        text = html.unescape(text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

def main():
    print("\n" + "="*80)
    print("FETCHING KEY SOP PAGES")
    print("="*80 + "\n")
    
    all_pages = {}
    
    # 1. Manual Reconciliation Checks (known ID)
    page_id = "169412024"
    content = fetch_page_by_id(page_id)
    if content:
        all_pages['manual_recon_checks'] = content
        
        # Save files
        json_file = f"sop_manual_recon_checks_{page_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved to: {json_file}")
        
        # Extract readable text
        readable = extract_readable_text(content['content'])
        txt_file = f"sop_manual_recon_checks_{page_id}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {content['title']}\n")
            f.write(f"URL: {content['url']}\n")
            f.write("="*80 + "\n\n")
            f.write(readable)
        print(f"   📄 Readable text: {txt_file}\n")
    
    # 2. Search for "Daily Operations: How to Label & Reconcile"
    print("\n" + "-"*80)
    page_id = search_for_page("Daily Operations Label Reconcile")
    if page_id:
        content = fetch_page_by_id(page_id)
        if content:
            all_pages['daily_operations'] = content
            
            json_file = f"sop_daily_operations_{page_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved to: {json_file}")
            
            readable = extract_readable_text(content['content'])
            txt_file = f"sop_daily_operations_{page_id}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {content['title']}\n")
                f.write(f"URL: {content['url']}\n")
                f.write("="*80 + "\n\n")
                f.write(readable)
            print(f"   📄 Readable text: {txt_file}\n")
    
    # 3. Search for "Labeling Bank Transactions"
    print("\n" + "-"*80)
    page_id = search_for_page("Labeling Bank Transactions")
    if page_id:
        content = fetch_page_by_id(page_id)
        if content:
            all_pages['labeling'] = content
            
            json_file = f"sop_labeling_{page_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved to: {json_file}")
            
            readable = extract_readable_text(content['content'])
            txt_file = f"sop_labeling_{page_id}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {content['title']}\n")
                f.write(f"URL: {content['url']}\n")
                f.write("="*80 + "\n\n")
                f.write(readable)
            print(f"   📄 Readable text: {txt_file}\n")
    
    print("\n" + "="*80)
    print(f"✅ DONE! Fetched {len(all_pages)} pages")
    print("="*80 + "\n")
    
    # Print summary
    for key, page in all_pages.items():
        print(f"📄 {page['title']}")
        print(f"   🔗 {page['url']}")
        print(f"   📊 {len(page['content'])} characters")
        print()

if __name__ == "__main__":
    # Check if BeautifulSoup is available
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("⚠️  BeautifulSoup not found. Installing...")
        import subprocess
        subprocess.check_call(['pip3', 'install', 'beautifulsoup4'])
        from bs4 import BeautifulSoup
    
    main()

