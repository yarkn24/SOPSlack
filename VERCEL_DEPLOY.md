# Vercel Deployment with Gemini AI 🚀

## Why Vercel?
✅ **Free tier** - Unlimited bandwidth  
✅ **Serverless Functions** - API endpoints with Python  
✅ **Environment Variables** - Secure API key storage  
✅ **Auto Deploy** - GitHub integration  
✅ **Global CDN** - Fast worldwide  

## 🎯 Quick Deploy

### Step 1: Push to GitHub
```bash
cd /Users/yarkin.akcil/Documents/GitHub/SOPSlack
git add .
git commit -m "Add Vercel serverless functions with Gemini AI"
git push origin main
```

### Step 2: Deploy to Vercel

1. **Go to Vercel:** https://vercel.com/signup
2. **Sign in with GitHub**
3. **Import Repository:**
   - Click "Add New" → "Project"
   - Select `SOPSlack` repository
   - Click "Import"

4. **Configure:**
   - Framework Preset: **Other**
   - Root Directory: `./`
   - Build Command: (leave empty)
   - Output Directory: `./`

5. **Add Environment Variable:**
   - Click "Environment Variables"
   - Name: `GEMINI_API_KEY`
   - Value: `AIzaSyDB7pkq0ssPKuZ6_vqP9HhnglYWhat3cNA`
   - Click "Add"

6. **Deploy:**
   - Click "Deploy"
   - Wait ~1 minute
   - Get your URL: `https://your-project.vercel.app`

## 🎨 Features

### ✅ Rule-Based Predictions
- Fast, instant results
- No API calls needed
- 30+ transaction types

### ✅ AI-Powered Predictions (Gemini Pro)
- For unknown transactions
- Pattern recognition
- Continuous learning

### ✅ Full SOP Integration
- All reconciliation steps
- Direct Confluence links
- Additional reference SOPs

## 📊 How It Works

```
User Input (CSV/Text)
    ↓
Frontend (predictor.js)
    ↓
Vercel Serverless Function (api/analyze.py)
    ↓
1. Try Rule-Based First
2. If Unknown → Ask Gemini Pro
    ↓
Return Result with SOP Content
```

## 🧪 Testing

### Local Test:
```bash
vercel dev
```
Then open: http://localhost:3000

### Production Test:
After deployment, visit your Vercel URL

## 🔒 Security

- ✅ API key stored as environment variable
- ✅ Never exposed in client-side code
- ✅ CORS enabled for your domain only
- ✅ Rate limiting by Vercel

## 📝 Project Structure

```
SOPSlack/
├── index.html              # Web interface
├── predictor.js            # Frontend logic
├── sop_data.json          # SOP database
├── api/
│   ├── analyze.py         # Serverless function
│   └── requirements.txt   # Python dependencies
├── complete_sop_mapping.py # SOP mapping
├── vercel.json            # Vercel config
└── .env                   # Local API keys (NOT committed)
```

## 🎯 Next Steps After Deploy

1. **Test the site:** Visit your Vercel URL
2. **Try some transactions:** Use the sample data
3. **Check AI predictions:** Look for "ML ile buldum" labels
4. **Monitor usage:** Check Vercel dashboard

## 💡 Tips

- **Free tier limits:** 
  - 100 GB bandwidth/month
  - 100 hours serverless execution/month
  - More than enough for internal tools

- **Custom domain (optional):**
  - Go to Vercel project settings
  - Add your domain
  - Update DNS records

- **Auto-deploy:**
  - Every push to `main` branch
  - Automatically deploys to Vercel
  - No manual steps needed

## 🆘 Troubleshooting

### Issue: API not working
- Check environment variables in Vercel dashboard
- Verify Gemini API key is correct
- Check function logs in Vercel

### Issue: CORS errors
- Add your domain to allowed origins
- Check browser console for details

### Issue: Slow predictions
- Rule-based is instant
- AI predictions take 2-5 seconds (normal)
- Consider caching frequent patterns

## 📧 Support

- Vercel Docs: https://vercel.com/docs
- Gemini API: https://ai.google.dev/docs

---

**Ready to deploy?** Follow Step 1-2 above! 🚀

