#!/usr/bin/env python3
"""
Fetch ALL Reconciliation SOP pages from Confluence
Based on the Reconciliations & Reporting section
"""
import os
from dotenv import load_dotenv
from atlassian import Confluence
import json
import re
from bs4 import BeautifulSoup
import time

load_dotenv()

confluence = Confluence(
    url=os.environ.get("CONFLUENCE_URL", "https://gustohq.atlassian.net"),
    username=os.environ.get("CONFLUENCE_USERNAME"),
    password=os.environ.get("CONFLUENCE_API_TOKEN"),
    cloud=True
)

# All SOP pages from the screenshot
SOP_PAGES_TO_FETCH = [
    # Already have these
    "Daily Operations : How to Label & Reconcile",
    "Manual Reconciliation Checks",
    "Labeling Bank Transactions",
    
    # Need to fetch
    "Escalating Reconciliation Issues to Cross-Functional Stakeholders",
    "BAI File Reconciliations",
    "Timeline of Expected Reconciliations",
    "Repayment Reporter Tool SOP",
    "How to Create a New Electronic Payment",
    "Microvariance Adjuster Tool",
    "Reporting Data Corrector",
    "Reconciliation Queue & Dashboard Overview",
    "Daily Bank Transaction Reconciliation by Bank Transaction Type",
    "Run Reconciler SOP for Electronic Payments",
    "NACHA Batch codes",
    "Reconciling EFT Debit Payments",
    "Manual Reconciliation by Agency",
    "Letter of Indemnity Process and Reconciliation",
    "How to use the Bulk Actions Tool SOP",
    "Bank Transaction Validator Alert",
    "Reconciling dLocal transactions manually",
    "Lockbox Investigations",
    "International Contractor Payment Funding",
    "Update Reconciliation Cutoff Date",
    "Unintended Overpayment Account Use Cases",
    "Transmission Reconciliation Alerts",
    "Zero Balance Transfer Reconciliation",
    "Double Cashed Checks",
    "Aged Bank Transactions",
    "End of Quarter Issues",
    "Unreconciled Transactions Due to Blueridge Ops Microvariance Write-offs",
    "Modern Treasury",
    "Manual Customer Cash Completeness Checks",
    "Customer Cash Completeness Checks",
]

def search_page(title_query):
    """Search for a page."""
    try:
        # Clean up title for search
        search_term = title_query.replace(":", "").replace("&", "")
        results = confluence.cql(
            f'space="PlatformOperations" AND type=page AND title~"{search_term}"',
            limit=3
        )
        
        if results and 'results' in results:
            for result in results['results']:
                content = result.get('content', {})
                found_title = content.get('title')
                # Fuzzy match
                if title_query.lower() in found_title.lower() or found_title.lower() in title_query.lower():
                    return content.get('id'), found_title
        
        return None, None
    except Exception as e:
        print(f"  ❌ Error searching: {e}")
        return None, None

def fetch_page(page_id):
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
        print(f"  ❌ Error fetching: {e}")
        return None

def extract_text(html_content):
    """Extract readable text."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except:
        text = re.sub(r'<[^>]+>', '\n', html_content)
        import html
        text = html.unescape(text)
        return text.strip()

def main():
    print("\n" + "="*80)
    print("FETCHING ALL RECONCILIATION SOP PAGES")
    print("="*80 + "\n")
    
    fetched = []
    not_found = []
    
    for i, page_title in enumerate(SOP_PAGES_TO_FETCH, 1):
        print(f"[{i}/{len(SOP_PAGES_TO_FETCH)}] Searching: {page_title}")
        
        page_id, found_title = search_page(page_title)
        
        if page_id:
            print(f"  ✅ Found: {found_title} (ID: {page_id})")
            
            content = fetch_page(page_id)
            
            if content:
                # Save JSON
                safe_name = re.sub(r'[^\w\s-]', '', page_title).replace(' ', '_').lower()
                json_file = f"sop_{safe_name}_{page_id}.json"
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                
                # Save readable text
                readable = extract_text(content['content'])
                txt_file = f"sop_{safe_name}_{page_id}.txt"
                
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {content['title']}\n")
                    f.write(f"URL: {content['url']}\n")
                    f.write("="*80 + "\n\n")
                    f.write(readable)
                
                print(f"  💾 Saved: {json_file}")
                print(f"  📄 Text: {txt_file}")
                
                fetched.append({
                    'query': page_title,
                    'found': found_title,
                    'id': page_id,
                    'url': content['url']
                })
            
        else:
            print(f"  ⚠️  Not found")
            not_found.append(page_title)
        
        print()
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully fetched: {len(fetched)}")
    print(f"⚠️  Not found: {len(not_found)}\n")
    
    if fetched:
        print("Fetched pages:")
        for item in fetched:
            print(f"  • {item['found']}")
            print(f"    {item['url']}")
    
    if not_found:
        print("\nNot found:")
        for title in not_found:
            print(f"  • {title}")
    
    # Save master index
    with open('sop_master_index.json', 'w', encoding='utf-8') as f:
        json.dump({
            'fetched': fetched,
            'not_found': not_found,
            'total_queried': len(SOP_PAGES_TO_FETCH),
            'success_count': len(fetched),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)
    
    print("\n📚 Master index saved: sop_master_index.json")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing BeautifulSoup...")
        import subprocess
        subprocess.check_call(['pip3', 'install', '-q', 'beautifulsoup4'])
        from bs4 import BeautifulSoup
    
    main()

