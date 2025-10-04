# SOPSlack

Slack entegrasyonu ile Atlassian ürünleri (Jira, Confluence) için SOP (Standard Operating Procedure) yönetim sistemi.

## Özellikler

- 🔗 Slack entegrasyonu
- 📝 Jira ve Confluence entegrasyonu
- 🤖 MCP (Model Context Protocol) desteği
- 📋 SOP yönetimi ve takibi

## Gereksinimler

- Python 3.8+
- Node.js 18+
- Slack Workspace
- Atlassian hesabı (Jira/Confluence)

## Kurulum

### 1. Depoyu klonlayın
```bash
git clone https://github.com/[kullanıcı-adınız]/SOPSlack.git
cd SOPSlack
```

### 2. Python bağımlılıklarını yükleyin
```bash
pip install -r requirements.txt
```

### 3. Ortam değişkenlerini ayarlayın
`.env` dosyası oluşturun:
```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_API_TOKEN=your-confluence-api-token
```

### 4. MCP Sunucusunu Başlatın
```bash
python mcp_server.py
```

## MCP Atlassian Entegrasyonu

Bu proje, MCP (Model Context Protocol) kullanarak Atlassian hizmetlerine erişim sağlar.

### MCP Sunucusu Kurulumu

1. MCP sunucu paketlerini yükleyin:
```bash
npm install -g @modelcontextprotocol/server-atlassian
```

2. MCP yapılandırma dosyasını düzenleyin (`mcp.json`):
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-atlassian"],
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

3. MCP sunucusunu test edin:
```bash
npx @modelcontextprotocol/server-atlassian
```

## Kullanım

### Slack Komutları

- `/sop create` - Yeni SOP oluştur
- `/sop list` - SOP'ları listele
- `/sop search [arama terimi]` - SOP ara
- `/sop sync` - Jira ve Confluence ile senkronize et

### API Endpoints

- `GET /api/sops` - Tüm SOP'ları getir
- `POST /api/sops` - Yeni SOP oluştur
- `GET /api/sops/:id` - Belirli bir SOP'u getir
- `PUT /api/sops/:id` - SOP güncelle
- `DELETE /api/sops/:id` - SOP sil

## Proje Yapısı

```
SOPSlack/
├── src/
│   ├── slack/          # Slack entegrasyonu
│   ├── atlassian/      # Jira ve Confluence entegrasyonu
│   ├── mcp/            # MCP sunucu yapılandırması
│   └── api/            # REST API
├── tests/              # Test dosyaları
├── config/             # Yapılandırma dosyaları
├── docs/               # Dokümantasyon
├── .env.example        # Örnek ortam değişkenleri
├── requirements.txt    # Python bağımlılıkları
└── README.md           # Bu dosya
```

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## Lisans

MIT License

## İletişim

Proje Sahibi - [@your-username](https://github.com/your-username)

Proje Linki: [https://github.com/your-username/SOPSlack](https://github.com/your-username/SOPSlack)
