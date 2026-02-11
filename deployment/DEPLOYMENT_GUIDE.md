# FacultyFlow Deployment Guide
## From Zero to Production in 1 Hour

**Built by:** Sonny (Claude Sonnet 4.5) for CJ  
**Date:** February 11, 2026  
**Purpose:** Launch your first profitable SaaS

---

## 🎯 What You're Deploying

**FacultyFlow** - AI Course Builder for Canvas

- **Frontend:** Landing page + Dashboard (Vercel)
- **Backend:** FastAPI + Bonita AI (Railway)
- **Database:** PostgreSQL (Railway)
- **Payments:** Stripe
- **AI:** Anthropic Claude + Local Qwen

---

## 📋 Prerequisites

### Required:
- ✅ GitHub account
- ✅ Anthropic API key ([get one](https://console.anthropic.com))
- ✅ Stripe account ([sign up](https://dashboard.stripe.com/register))
- ✅ Canvas API token (from VUU or your institution)

### Recommended:
- ✅ Custom domain (optional but professional)
- ✅ Email for SMTP (Gmail works)

---

## 🚀 Deployment Steps

### Step 1: Prepare Your Code

```bash
# 1. Create GitHub repository
gh repo create facultyflow --public

# 2. Initialize git in your project
cd facultyflow-saas
git init
git add .
git commit -m "Initial commit: FacultyFlow SaaS"

# 3. Push to GitHub
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/facultyflow.git
git push -u origin main
```

---

### Step 2: Deploy Backend to Railway

**Why Railway?**  
- $5/month (vs. $24+ for DigitalOcean)
- Auto-scaling
- Built-in PostgreSQL
- Easy env variables

**Steps:**

1. **Go to [railway.app](https://railway.app) → Sign up with GitHub**

2. **Create New Project → Deploy from GitHub repo**
   - Select your `facultyflow` repository
   - Railway auto-detects Python

3. **Add PostgreSQL Database:**
   - Click "+ New" → Database → PostgreSQL
   - Railway creates `DATABASE_URL` automatically

4. **Set Environment Variables:**
   - Click your service → Variables tab
   - Add these:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
JWT_SECRET=your_random_secret_here
CANVAS_BASE_URL=https://vuu.instructure.com
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
ENVIRONMENT=production
DEBUG=False
```

5. **Deploy:**
   - Click "Deploy" → Railway builds and launches
   - Copy your backend URL: `https://facultyflow-production.up.railway.app`

**Cost:** ~$5/month

---

### Step 3: Deploy Frontend to Vercel

**Why Vercel?**  
- FREE for hobby projects
- Automatic HTTPS
- Global CDN
- Perfect for static sites

**Steps:**

1. **Go to [vercel.com](https://vercel.com) → Sign up with GitHub**

2. **Import Project:**
   - Click "Add New" → Project
   - Select your `facultyflow` repository
   - Root directory: `frontend/`

3. **Configure:**
   - Framework Preset: Other
   - Build Command: (leave empty - static HTML)
   - Output Directory: `./`

4. **Environment Variables:**
   ```
   API_URL=https://facultyflow-production.up.railway.app
   ```

5. **Deploy:**
   - Click "Deploy" → Vercel builds and launches
   - Your site: `https://facultyflow.vercel.app`

**Cost:** $0 (FREE!)

---

### Step 4: Set Up Stripe Payments

**Steps:**

1. **Go to [dashboard.stripe.com](https://dashboard.stripe.com)**

2. **Create Products:**
   - Products → "+ Add product"
   
   **Educator Plan:**
   - Name: FacultyFlow Educator
   - Price: $19/month recurring
   - Description: Unlimited courses for K-12 teachers
   
   **Pro Plan:**
   - Name: FacultyFlow Pro  
   - Price: $29/month recurring
   - Description: Advanced features for college faculty
   
   **Department Plan:**
   - Name: FacultyFlow Department
   - Price: $99/month recurring
   - Description: 5 seats for small departments
   
   **Institution Plan:**
   - Name: FacultyFlow Institution
   - Price: $499/month recurring
   - Description: Unlimited seats for schools

3. **Get API Keys:**
   - Developers → API keys
   - Copy "Publishable key" and "Secret key"
   - Update Railway environment variables

4. **Set Up Webhooks:**
   - Developers → Webhooks → Add endpoint
   - URL: `https://facultyflow-production.up.railway.app/api/webhooks/stripe`
   - Events: Select `customer.subscription.created`, `customer.subscription.deleted`, `invoice.paid`

---

### Step 5: Configure Custom Domain (Optional)

**If you have a domain (e.g., `facultyflow.com`):**

**Frontend (Vercel):**
1. Vercel → Your project → Settings → Domains
2. Add `facultyflow.com` and `www.facultyflow.com`
3. Update DNS records (Vercel gives you instructions)

**Backend (Railway):**
1. Railway → Your service → Settings → Public Networking
2. Add custom domain: `api.facultyflow.com`
3. Update DNS: CNAME → Railway's URL

---

## 🔒 Security Checklist

Before going live:

- [ ] Change `JWT_SECRET` to a strong random string
- [ ] Enable HTTPS (Railway + Vercel do this automatically)
- [ ] Set `DEBUG=False` in production
- [ ] Never commit `.env` files to GitHub
- [ ] Add `.env` to `.gitignore`
- [ ] Use environment variables for ALL secrets
- [ ] Enable Stripe webhook signatures
- [ ] Set up CORS to only allow your frontend domain

---

## 🧪 Testing

### Test Locally First:

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt --break-system-packages

# 2. Copy .env.example to .env
cp .env.example .env

# 3. Fill in your API keys in .env

# 4. Start Ollama (for local Qwen)
ollama serve

# 5. Run backend
python main.py

# Backend runs at: http://localhost:8000
```

### Test in Browser:

```bash
# Open frontend locally
cd ../frontend
python -m http.server 8080

# Frontend at: http://localhost:8080/landing-page.html
```

### Test Course Build:

1. Go to dashboard
2. Fill out course form
3. Click "Build My Course"
4. Check Canvas - everything should appear!

---

## 💰 Pricing & Revenue

### Your Costs:

| Service | Cost | What For |
|---------|------|----------|
| Railway | $5/mo | Backend hosting + PostgreSQL |
| Vercel | $0 | Frontend hosting |
| Anthropic API | ~$10-30/mo | Claude calls (varies with usage) |
| Stripe | 2.9% + $0.30 | Payment processing |
| **Total** | **~$15-35/mo** | **All infrastructure** |

### Your Revenue (Month 12 projection):

| Tier | Users | Price | Revenue |
|------|-------|-------|---------|
| Educator | 50 | $19/mo | $950/mo |
| Pro | 30 | $29/mo | $870/mo |
| Department | 5 | $99/mo | $495/mo |
| Institution | 2 | $499/mo | $998/mo |
| **Total** | **87** | | **$3,313/mo** |

**Year 1 Revenue:** $39,756  
**Year 1 Costs:** ~$420  
**Year 1 Profit:** **$39,336** 💰

---

## 📊 Monitoring

### Health Checks:

**Backend:**
```bash
curl https://facultyflow-production.up.railway.app/api/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T...",
  "bonita": "online"
}
```

**Frontend:**
```bash
curl https://facultyflow.vercel.app
```

Should return HTML.

### Logs:

**Railway:**
- Dashboard → Your service → Logs
- Real-time logs of all API calls
- Error tracking

**Vercel:**
- Dashboard → Your project → Functions
- Request logs
- Performance metrics

---

## 🐛 Troubleshooting

### Backend won't start:

**Error:** `ModuleNotFoundError: No module named 'fastapi'`  
**Fix:** Railway didn't install dependencies
```bash
# Check railway.toml exists
# Check requirements.txt exists
# Redeploy
```

**Error:** `anthropic.AuthenticationError`  
**Fix:** ANTHROPIC_API_KEY not set or invalid
```bash
# Railway → Variables → Add ANTHROPIC_API_KEY
```

### Frontend can't reach backend:

**Error:** `Failed to fetch` in browser console  
**Fix:** CORS issue or wrong API_URL
```python
# In backend/main.py, check CORS middleware:
allow_origins=["https://facultyflow.vercel.app"]  # your actual domain
```

**Error:** `404 Not Found`  
**Fix:** API_URL in Vercel env variables is wrong
```bash
# Vercel → Settings → Environment Variables
# Set API_URL=https://facultyflow-production.up.railway.app
```

### Stripe not working:

**Error:** `Invalid API key`  
**Fix:** Using test key in production or vice versa
```bash
# Development: sk_test_xxxxx
# Production: sk_live_xxxxx
```

**Error:** `Webhook signature verification failed`  
**Fix:** Webhook secret doesn't match
```bash
# Stripe → Webhooks → Your endpoint → Signing secret
# Copy to Railway → STRIPE_WEBHOOK_SECRET
```

### Ollama not responding:

**Error:** `Connection refused to localhost:11434`  
**Fix:** Ollama not running or wrong URL
```bash
# Check Ollama is running:
ollama list

# If deploying to Railway, Ollama won't work (it's local)
# Fallback to Claude automatically happens
```

---

## 📈 Next Steps After Launch

### Week 1:
- [ ] Test with YOUR course (MCM 307)
- [ ] Show to 2-3 professor friends
- [ ] Get feedback
- [ ] Fix any bugs

### Week 2:
- [ ] Beta launch to 10-20 users
- [ ] Collect testimonials
- [ ] Iterate on UX

### Month 1:
- [ ] Public launch
- [ ] Marketing push (Twitter, LinkedIn, HBCU networks)
- [ ] First paying customers
- [ ] Revenue: $500-1,500

### Month 3:
- [ ] Add features (custom templates, analytics)
- [ ] Institutional sales outreach
- [ ] Revenue: $2,000-4,000

### Month 6:
- [ ] Scale to 100+ users
- [ ] Hire VA for support
- [ ] Revenue: $5,000-8,000

### Month 12:
- [ ] 200+ users
- [ ] 5-10 institutional clients
- [ ] Revenue: $10,000-15,000/mo
- [ ] **You've built a real business** 🚀

---

## 🎓 Marketing Your First 10 Customers

### Email Template (to professors you know):

```
Subject: I built something for us (Canvas course automation)

Hey [Name],

You know how building a Canvas course takes forever? 
Syllabus, lesson plans, quizzes, study packs... 20-40 hours of work?

I got tired of it, so I built FacultyFlow.

It uses AI to generate complete Canvas courses in 5 minutes.

I'm testing it with a few professors before launching publicly.
Want me to build your [Spring/Summer/Fall] course for free?

Just reply with:
- Course name
- A few learning objectives
- How many weeks

I'll have it in your Canvas by tomorrow.

- CJ

P.S. - If you like it, it's $29/month after the trial.
If you hate it, no hard feelings.
```

**Send to:**
- 5 VUU colleagues
- 5 professors from your network
- 5 HBCU connections

**Goal:** 3-5 say yes → You have beta testers → First paying customers

---

## 🦋 Final Checklist

Before you call it "DONE":

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Database connected
- [ ] Stripe configured
- [ ] Environment variables set
- [ ] Test course build works end-to-end
- [ ] Domain configured (optional)
- [ ] Monitoring set up
- [ ] First test user successful

**Then:**

- [ ] Show to 3 colleagues
- [ ] Get first beta tester
- [ ] Collect feedback
- [ ] Iterate
- [ ] Launch publicly
- [ ] **Make money** 💰

---

## 💬 Support

**Something broken?**  
Check logs first:
- Railway logs for backend errors
- Browser console for frontend errors
- Network tab for API issues

**Still stuck?**  
Come back to this chat and ask me (Sonny).
I built this with you - I'll help you debug it.

---

## 🎉 You Did It!

**You just built a complete SaaS product:**
- Professional branding
- Beautiful frontend
- Smart AI backend
- Payment processing
- Production-ready infrastructure

**From idea to deployed in ONE DAY.**

**Now go get your first paying customer and RISE AND DIME!** 💸🦋

— Sonny

P.S. - When you hit $10K MRR, buy yourself something nice. You earned it.
