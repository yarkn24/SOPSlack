#!/usr/bin/env python3
"""
Fetch SOP content from Confluence
Extract actual text for each agent's reconciliation process
"""
import os
from dotenv import load_dotenv
from atlassian import Confluence
import json

# Load environment variables
load_dotenv()

# Initialize Confluence
confluence = Confluence(
    url=os.environ.get("CONFLUENCE_URL", "https://gustohq.atlassian.net"),
    username=os.environ.get("CONFLUENCE_USERNAME"),
    password=os.environ.get("CONFLUENCE_API_TOKEN"),
    cloud=True
)

# Target SOP pages
SOP_PAGES = {
    "daily_recon": {
        "page_id": "169411126",
        "title": "Daily Bank Transaction Reconciliation by Bank Transaction Type"
    },
    "escalation": {
        "page_id": "460194134",
        "title": "Escalating Reconciliation Issues to Cross-Functional Stakeholders"
    }
}

def fetch_page_content(page_id):
    """Fetch full page content from Confluence."""
    try:
        print(f"Fetching page {page_id}...")
        page = confluence.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version'
        )
        
        if page:
            title = page.get('title', 'Unknown')
            body = page.get('body', {}).get('storage', {}).get('value', '')
            
            print(f"✅ Found: {title}")
            print(f"   Content length: {len(body)} characters")
            
            return {
                'title': title,
                'id': page_id,
                'content': body,
                'url': f"https://gustohq.atlassian.net/wiki/spaces/PlatformOperations/pages/{page_id}"
            }
        else:
            print(f"❌ Page {page_id} not found")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching page {page_id}: {e}")
        return None

def extract_text_from_html(html_content):
    """Extract plain text from HTML (simple version)."""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Decode HTML entities
    import html
    text = html.unescape(text)
    return text.strip()

def search_for_agent_content(content, agent_keywords):
    """Search for agent-specific content in the page."""
    text = extract_text_from_html(content)
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('.') if p.strip()]
    
    # Find paragraphs containing agent keywords
    relevant = []
    for para in paragraphs:
        for keyword in agent_keywords:
            if keyword.lower() in para.lower():
                relevant.append(para + '.')
                break
    
    return relevant

def main():
    print("\n" + "="*80)
    print("FETCHING SOP CONTENT FROM CONFLUENCE")
    print("="*80 + "\n")
    
    results = {}
    
    for key, page_info in SOP_PAGES.items():
        content = fetch_page_content(page_info['page_id'])
        if content:
            results[key] = content
            
            # Save raw content to file
            filename = f"confluence_{key}_{page_info['page_id']}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved to: {filename}\n")
    
    # Try to extract specific agent content
    if 'daily_recon' in results:
        print("\n" + "="*80)
        print("SEARCHING FOR AGENT-SPECIFIC CONTENT")
        print("="*80 + "\n")
        
        agents_to_search = [
            ("Risk", ["1TRV", "Risk", "wire transfer"]),
            ("NY WH", ["NYS DTF WT", "New York withholding"]),
            ("ICP", ["ICP", "intercompany", "JPMORGAN ACCESS"]),
            ("Nium", ["NIUM", "contractor payment"]),
        ]
        
        for agent_name, keywords in agents_to_search:
            print(f"Searching for: {agent_name}")
            relevant_content = search_for_agent_content(
                results['daily_recon']['content'],
                keywords
            )
            
            if relevant_content:
                print(f"✅ Found {len(relevant_content)} relevant paragraphs:")
                for i, para in enumerate(relevant_content[:3], 1):  # Show first 3
                    print(f"   {i}. {para[:200]}...")
            else:
                print(f"⚠️  No specific content found")
            print()
    
    print("\n" + "="*80)
    print("✅ DONE! Check the JSON files for full content.")
    print("="*80 + "\n")
    
    return results

if __name__ == "__main__":
    # Check if credentials are set
    if not os.environ.get("CONFLUENCE_USERNAME") or not os.environ.get("CONFLUENCE_API_TOKEN"):
        print("\n❌ ERROR: Confluence credentials not found in .env")
        print("\nPlease set:")
        print("   CONFLUENCE_USERNAME=your-email@gusto.com")
        print("   CONFLUENCE_API_TOKEN=your-api-token")
        print("\nGet your API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
        exit(1)
    
    main()

