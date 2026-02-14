# ⚡ QUICK START GUIDE

**Get ReadySetClass running in 5 minutes!**

---

## 🎯 3 COMMANDS TO RUN:

### 1. Run Database Migrations

```bash
cd ~/Desktop/readysetclass/backend

# Get your DATABASE_URL from Railway dashboard
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@containers-us-west-XXX.railway.app:XXXX/railway"

# Run migration
python run_migration.py
```

**Expected output:**
```
🔄 Connecting to database...
🔄 Running migration: 001_create_auth_tables.sql
✅ Migration completed successfully!
```

---

### 2. Create Your Admin Account

```bash
python create_admin.py
```

**Enter when prompted:**
- Email: `cj@vuu.edu` (or press Enter for default)
- Password: `[create a strong password]`
- Confirm password: `[same password]`

**Expected output:**
```
==================================================
✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!
==================================================
Email: cj@vuu.edu
User ID: 1
Role: admin

Login at: https://readysetclass.com/login.html
==================================================
```

**⚠️ SAVE YOUR PASSWORD IN A PASSWORD MANAGER!**

---

### 3. Login & Test

1. Go to: https://readysetclass.com/login.html
2. Enter your email and password
3. Click "Log In"
4. You should see the dashboard!

---

## ✅ VERIFY IT WORKS:

### Test 1: Create a Quiz
1. Click "📝 Create Quiz"
2. Select "✨ AI-Enhanced"
3. Enter:
   - Topic: "Week 1: Introduction to Media"
   - Description: "This quiz covers the basics of media literacy"
   - Grade Level: "College" (or any level)
4. Click "Generate Quiz with AI"
5. Review the questions
6. Click "Upload to Canvas" (if you have Canvas connected)

### Test 2: Install as Mobile App
**iPhone:**
- Safari → Share → Add to Home Screen

**Android:**
- Chrome → Menu → Install app

### Test 3: Mobile Features (NEW!)
**On Mobile Device:**
1. Install to home screen (see Test 2)
2. Open app → See bottom navigation at bottom
3. Create Quiz → Tap microphone button 🎤 on description field
4. Speak your quiz description → Watch it transcribe!
5. Create Syllabus → See photo upload option 📷
6. Test touch-friendly buttons (all 44px minimum)

### Test 4: Pricing Page
- Visit: https://readysetclass.com/pricing.html
- See new hero copy: "Reclaim your time"

---

## 🔧 CONFIGURE STRIPE (OPTIONAL - FOR PAYMENTS):

### Step 1: Get Stripe Keys

1. Go to: https://dashboard.stripe.com/apikeys
2. Copy "Secret key" (starts with `sk_live_...` or `sk_test_...`)
3. Go to: https://dashboard.stripe.com/webhooks
4. Create endpoint: `https://readysetclass-production.up.railway.app/api/stripe/webhook`
5. Copy "Signing secret" (starts with `whsec_...`)

### Step 2: Add to Railway

1. Go to Railway dashboard
2. Click your project → Variables
3. Add:
   ```
   STRIPE_SECRET_KEY=sk_test_XXX
   STRIPE_WEBHOOK_SECRET=whsec_XXX
   ```
4. Railway will auto-redeploy

### Step 3: Create Products in Stripe

1. Go to: https://dashboard.stripe.com/products
2. Create 3 products:
   - **Pro:** $29/month
   - **Team:** $99/month
   - **Enterprise:** $299/month
3. Copy each "Price ID" (starts with `price_`)

### Step 4: Update Frontend

Edit `frontend/pricing.html` line 116:
```javascript
const priceIds = {
    'pro': 'price_YOUR_PRO_PRICE_ID',
    'team': 'price_YOUR_TEAM_PRICE_ID'
};
```

Deploy:
```bash
cd ~/Desktop/readysetclass/frontend
vercel --prod
```

---

## 🎉 THAT'S IT!

**ReadySetClass is now:**
- ✅ Running in production
- ✅ Accepting logins
- ✅ Generating AI content
- ✅ Installable on mobile
- ✅ Ready for customers (once Stripe configured)

---

## 🐛 TROUBLESHOOTING:

### "Invalid credentials" when logging in:
- Make sure you created admin account (step 2 above)
- Check password is correct
- Try creating account again

### "Database not available":
- Check DATABASE_URL is set correctly in Railway
- Make sure migration ran successfully

### Quiz generation fails:
- Check Railway logs
- Verify GROQ_API_KEY is set in Railway

### Stripe checkout doesn't work:
- Make sure STRIPE_SECRET_KEY is set in Railway
- Check price IDs are updated in pricing.html
- Use test mode first (sk_test_...)

---

## 📞 NEED HELP?

Check these files:
- `MORNING_BRIEFING.md` - Full feature list
- `OVERNIGHT_BUILD_COMPLETE.md` - Original build notes

---

**Now go make some money! 💰**

— Q-Tip
