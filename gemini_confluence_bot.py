#!/usr/bin/env python3
"""
SOPSlack Bot with Gemini AI + Confluence Integration
Responds to Slack questions using Confluence documentation via MCP Atlassian
"""
import os
import json
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import google.generativeai as genai
from atlassian import Confluence

# Load environment variables
load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize Confluence
confluence = Confluence(
    url=os.environ.get("CONFLUENCE_URL"),
    username=os.environ.get("CONFLUENCE_USERNAME"),
    password=os.environ.get("CONFLUENCE_API_TOKEN"),
    cloud=True
)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

def search_confluence(query, space_key="PlatformOperations", limit=5):
    """Search Confluence for relevant documentation"""
    try:
        cql = f'space="{space_key}" AND type=page AND text~"{query}"'
        results = confluence.cql(cql, limit=limit)
        
        pages = []
        for result in results.get('results', []):
            content_data = result.get('content', {})
            page_id = content_data.get('id')
            title = content_data.get('title')
            
            if page_id and title:
                # Get page content
                try:
                    page = confluence.get_page_by_id(
                        page_id, 
                        expand='body.storage,version'
                    )
                    pages.append({
                        'id': page_id,
                        'title': title,
                        'url': f"{os.environ.get('CONFLUENCE_URL')}/pages/viewpage.action?pageId={page_id}",
                        'content': page.get('body', {}).get('storage', {}).get('value', '')[:2000]  # First 2000 chars
                    })
                except Exception as e:
                    print(f"Error fetching page {page_id}: {e}")
                    continue
        
        return pages
    except Exception as e:
        print(f"Confluence search error: {e}")
        return []

def create_context_from_pages(pages):
    """Create context string from Confluence pages"""
    if not pages:
        return "No relevant documentation found."
    
    context = "# Relevant Confluence Documentation\n\n"
    for page in pages:
        context += f"## {page['title']}\n"
        context += f"URL: {page['url']}\n\n"
        # Strip HTML tags for cleaner context
        clean_content = page['content'].replace('<p>', '\n').replace('</p>', '\n')
        clean_content = clean_content.replace('<br/>', '\n').replace('<br>', '\n')
        context += f"{clean_content[:1000]}...\n\n"
        context += "---\n\n"
    
    return context

def ask_gemini(question, context):
    """Ask Gemini with Confluence context"""
    prompt = f"""You are a helpful assistant for Gusto's Platform Operations team. 
You have access to the team's Confluence documentation.

Based on the following Confluence documentation, please answer the user's question.
If the documentation doesn't contain the answer, say so honestly.
Always cite the relevant Confluence pages in your answer.

CONFLUENCE DOCUMENTATION:
{context}

USER QUESTION: {question}

Please provide a clear, helpful answer in Turkish. Include relevant links to Confluence pages."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini API hatası: {str(e)}"

@app.event("app_mention")
def handle_mentions(event, say, logger):
    """Handle @mentions of the bot"""
    try:
        user = event['user']
        text = event['text']
        
        # Remove bot mention from text
        question = text.split('>', 1)[-1].strip() if '>' in text else text
        
        if not question or len(question) < 3:
            say(f"Merhaba <@{user}>! Bana Platform Operations hakkında bir soru sorun. Confluence dökümanlarından cevap vereceğim! 🤖")
            return
        
        # Send thinking message
        say(f"🔍 <@{user}> için Confluence dökümanlarında arıyorum: *{question}*")
        
        # Search Confluence
        pages = search_confluence(question)
        
        if not pages:
            say(f"❌ <@{user}>, '{question}' hakkında Confluence'da bir şey bulamadım. Farklı kelimeler deneyebilir misin?")
            return
        
        # Create context and ask Gemini
        context = create_context_from_pages(pages)
        answer = ask_gemini(question, context)
        
        # Format response with sources
        response = f"*Cevap:*\n{answer}\n\n"
        response += f"📚 *Kaynaklar:*\n"
        for page in pages:
            response += f"• <{page['url']}|{page['title']}>\n"
        
        say(response)
        
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(f"❌ Bir hata oluştu: {str(e)}")

@app.command("/confluence")
def handle_confluence_search(ack, command, say):
    """Handle /confluence slash command for direct search"""
    ack()
    
    text = command.get('text', '').strip()
    
    if not text:
        say("📖 Kullanım: `/confluence [arama terimi]`\nÖrnek: `/confluence reconciliation nasıl yapılır`")
        return
    
    # Search Confluence
    say(f"🔍 Confluence'da arıyorum: *{text}*")
    pages = search_confluence(text)
    
    if not pages:
        say(f"❌ '{text}' hakkında bir şey bulamadım.")
        return
    
    # Return search results
    response = f"*'{text}' için bulunan dökümanlar:*\n\n"
    for i, page in enumerate(pages, 1):
        response += f"{i}. <{page['url']}|{page['title']}>\n"
    
    say(response)

@app.command("/sop")
def handle_sop_command(ack, command, say):
    """Handle /sop slash command"""
    ack()
    
    text = command.get('text', '').strip()
    
    if not text:
        say("""
🤖 *SOPSlack Komutları:*
• `/sop ask [soru]` - AI'ya Platform Operations sorusu sor
• `/confluence [arama]` - Confluence'da doğrudan ara
• Bot'u mention ederek soru sorabilirsiniz: @SOPSlack [soru]

*Örnek Sorular:*
• Reconciliation nasıl yapılır?
• BAI file nedir?
• Double cashed check nasıl handle edilir?
• Payment investigation hashtags nelerdir?
        """)
        return
    
    if text.startswith('ask'):
        question = text.replace('ask', '').strip()
        if not question:
            say("❌ Lütfen bir soru sorun. Örnek: `/sop ask reconciliation nasıl yapılır`")
            return
        
        say(f"🔍 Confluence dökümanlarında arıyorum: *{question}*")
        pages = search_confluence(question)
        
        if not pages:
            say(f"❌ '{question}' hakkında bir şey bulamadım.")
            return
        
        context = create_context_from_pages(pages)
        answer = ask_gemini(question, context)
        
        response = f"*Cevap:*\n{answer}\n\n"
        response += f"📚 *Kaynaklar:*\n"
        for page in pages:
            response += f"• <{page['url']}|{page['title']}>\n"
        
        say(response)
    else:
        say("❌ Bilinmeyen komut. `/sop` yazarak yardımı görebilirsiniz.")

@app.message("hello")
def handle_hello(message, say):
    """Handle 'hello' messages"""
    say(f"Merhaba <@{message['user']}>! 👋 Bana Platform Operations hakkında sorular sorabilirsin!")

@app.event("message")
def handle_message_events(body, logger):
    """Log all message events for debugging"""
    logger.info(body)

if __name__ == "__main__":
    # Check required environment variables
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET", 
        "SLACK_APP_TOKEN",
        "GEMINI_API_KEY",
        "CONFLUENCE_URL",
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Eksik environment variables: {', '.join(missing_vars)}")
        print("\n.env dosyasını oluşturun ve şu değişkenleri ekleyin:")
        for var in missing_vars:
            print(f"  {var}=...")
        exit(1)
    
    # Start Socket Mode
    app_token = os.environ.get("SLACK_APP_TOKEN")
    
    print("=" * 50)
    print("🚀 SOPSlack Bot Starting...")
    print("=" * 50)
    print("✅ Gemini API: Configured")
    print("✅ Confluence: Connected")
    print("✅ Slack: Socket Mode")
    print("\nBot is ready! Mention me in Slack or use /sop commands")
    print("=" * 50)
    
    handler = SocketModeHandler(app, app_token)
    handler.start()
