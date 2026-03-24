# ScopeDeals — Self-Running Smart Telescope Price Tracker

A fully automated price comparison site for smart telescopes and astrophotography gear. Prices update automatically twice a week via GitHub Actions, and the site deploys itself to Netlify.

## How It Works

```
GitHub Actions (Mon & Thu 6AM UTC)
    │
    ├── scripts/update_prices.py   ← Scrapes Amazon + retailer prices
    │       │
    │       └── Updates data/products.json
    │
    ├── scripts/build_site.py      ← Generates public/index.html
    │
    ├── git commit + push          ← Saves updated prices to repo
    │
    └── Deploy to Netlify          ← Site goes live automatically
```

**Zero manual work required** after initial setup.

---

## One-Time Setup (15 minutes)

### 1. Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/scopedeals.git
git push -u origin main
```

### 2. Connect to Netlify

1. Go to [app.netlify.com](https://app.netlify.com) → "Add new site" → "Import an existing project"
2. Connect your GitHub repo
3. Set **Publish directory** to `public`
4. Leave **Build command** empty (GitHub Actions handles builds)
5. Deploy — your site is live!

### 3. Get Your Netlify Credentials

1. Go to **Netlify** → User Settings → Applications → **Personal access tokens** → New
2. Copy the token — this is your `NETLIFY_AUTH_TOKEN`
3. Go to your site → Site configuration → General → **Site ID** — this is your `NETLIFY_SITE_ID`

### 4. Add GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → **New repository secret**

Add these secrets:

| Secret Name | Where to Get It |
|---|---|
| `NETLIFY_AUTH_TOKEN` | Netlify → User Settings → Personal access tokens |
| `NETLIFY_SITE_ID` | Netlify → Site configuration → Site ID |
| `AMAZON_CREDENTIAL_ID` | [Amazon Creators API](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction) |
| `AMAZON_CREDENTIAL_SECRET` | Same as above |
| `AMAZON_AFFILIATE_TAG` | Your Amazon Associates tag (e.g. `yourtag-20`) |

**Note:** Amazon credentials are optional. Without them, prices for Amazon products won't auto-update, but scraping from other retailers (High Point Scientific, Unistellar, Vaonis) will still work.

### 5. Test It

Go to GitHub → Actions → "Weekly Price Update & Deploy" → **Run workflow** (manual trigger)

Watch it run. If successful, your site is now self-maintaining!

---

## Managing Products

### Admin Panel

Open `templates/admin.html` in your browser (locally, not deployed). It has two tabs:

**Products tab:**
- Add, edit, delete products
- Import/Export JSON backups
- Generate JS code (legacy method)

**Affiliate Links tab:**
- See all products and their current affiliate URLs
- Paste affiliate links as you get approved by retailers
- One-click "Set Amazon Tag" to bulk-update all Amazon links
- Filter by retailer to focus on one program at a time

### Workflow for Adding Products

1. Open `admin.html` locally
2. Click **Import JSON** → load `data/products.json`
3. Add your new products via the form
4. Click **Export JSON** → save the file
5. Replace `data/products.json` in your repo with the exported file
6. `git add . && git commit -m "Added new products" && git push`
7. GitHub Actions will rebuild and deploy automatically

### Workflow for Setting Affiliate Links

1. Get approved by a retailer (Amazon, High Point Scientific, etc.)
2. Open `admin.html` → **Affiliate Links** tab
3. Paste your affiliate URLs for each product
4. For Amazon: click **Set Amazon Tag for All** and enter your tag
5. **Export JSON** → replace `data/products.json` → push to GitHub

---

## File Reference

```
scopedeals-auto/
├── .github/workflows/
│   └── update-prices.yml       # GitHub Actions schedule (Mon & Thu)
├── scripts/
│   ├── update_prices.py        # Price scraper (Amazon API + web scraping)
│   └── build_site.py           # Site generator (JSON → HTML)
├── data/
│   ├── products.json           # Product database (69 products)
│   └── price_history.json      # Auto-generated price history log
├── templates/
│   ├── site.html               # Site HTML template
│   └── admin.html              # Admin panel (use locally)
├── public/                     # Generated output (deployed to Netlify)
│   ├── index.html              # The live site
│   └── admin.html              # Admin panel (optional deploy)
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## Price Sources (54 of 69 products covered)

| Source | Products | Method |
|---|---|---|
| Amazon Creators API | 35 | API lookup by ASIN |
| High Point Scientific | 12 | Web scraping (JSON-LD) |
| Unistellar.com | 1 | Web scraping |
| Vaonis.com | 1 | Web scraping |
| Other retailers | 5 | Web scraping |
| Manual only | 15 | Edit products.json directly |

## Cost

- **GitHub Actions**: Free (2,000 minutes/month on free tier, each run uses ~2 min)
- **Netlify**: Free tier (100GB bandwidth, 300 build minutes/month)
- **Total: $0/month**

## Affiliate Programs to Join

| Retailer | Commission | Apply |
|---|---|---|
| Amazon Associates | 1-4% | [affiliate-program.amazon.com](https://affiliate-program.amazon.com) |
| High Point Scientific | Competitive | [highpointscientific.com/affiliate](https://www.highpointscientific.com/high-point-scientific-affiliate-program-faq) |
| OPT Telescopes | Competitive | [optcorp.com/affiliate](https://optcorp.com/pages/opt-affiliate-program) |
| Unistellar | Per-sale | [unistellar.com/affiliate](https://www.unistellar.com/affiliate-program/) |
| B&H Photo | 2-8% | Via ShareASale / CJ |
| Agena Astro | Competitive | [agenaastro.com/affiliate](https://agenaastro.com/affiliate-program) |
