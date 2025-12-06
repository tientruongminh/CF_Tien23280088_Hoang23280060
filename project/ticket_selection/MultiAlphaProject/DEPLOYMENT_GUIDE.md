# Deployment Guide - Multi-Alpha Dashboard

## 🚀 3 OPTIONS TO DEPLOY

---

## OPTION 1: LOCAL DEPLOYMENT (Easiest)

**Best for:** Testing, development, personal use

### Step 1: Install Dependencies

```bash
cd /home/tiencd123456/CF_Tien23280088_Hoang23280060-1
pip install -r requirements.txt
```

### Step 2: Run Dashboard

```bash
cd project/ticket_selection/MultiAlphaProject
streamlit run app.py
```

**Access at:** http://localhost:8501

### Keep Running (Background)

```bash
# Using nohup
nohup streamlit run app.py --server.port 8501 &

# Or using screen
screen -S multi-alpha
streamlit run app.py
# Press Ctrl+A then D to detach
```

**Pros:** 
- ✅ Simple, fast
- ✅ Full control
- ✅ Free

**Cons:**
- ❌ Only accessible on your machine
- ❌ Stops when computer sleeps

---

## OPTION 2: STREAMLIT CLOUD (Recommended for Sharing)

**Best for:** Sharing with team, public access, FREE hosting

### Step 1: Prepare GitHub Repo

Your code is already on GitHub:
```
https://github.com/tientruongminh/CF_Tien23280088_Hoang23280060
Branch: multi-alpha-final
```

### Step 2: Create Streamlit Account

1. Visit: https://streamlit.io/cloud
2. Sign up with GitHub account
3. Authorize Streamlit to access your repos

### Step 3: Deploy

1. Click **"New app"**
2. Select:
   - **Repository:** `tientruongminh/CF_Tien23280088_Hoang23280060`
   - **Branch:** `multi-alpha-final`
   - **Main file path:** `project/ticket_selection/MultiAlphaProject/app.py`
3. Click **"Deploy"**

**Wait 2-5 minutes** for deployment.

### Step 4: Configure Secrets (for Gemini AI)

1. In Streamlit Cloud dashboard → App settings
2. Go to **Secrets**
3. Add (if needed):
```toml
[gemini]
api_key = "your-gemini-api-key-here"
```

### Step 5: Access Your App

**URL will be:** `https://cf-tien-hoang-multi-alpha.streamlit.app`

**Share this link** with anyone!

### Important: Add .gitignore

Create `.streamlit/config.toml`:
```toml
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

**Pros:**
- ✅ FREE hosting
- ✅ Public URL (shareable)
- ✅ Auto-updates from GitHub
- ✅ No server management

**Cons:**
- ❌ Resource limits (1GB RAM)
- ❌ App sleeps after inactivity (free tier)
- ❌ Large data files may be slow

---

## OPTION 3: CUSTOM SERVER DEPLOYMENT

**Best for:** Production, always-on, large data

### 3A: Deploy on Your Server (VPS/Cloud)

**Providers:** DigitalOcean, AWS, Google Cloud, Azure

#### Step 1: Setup Server

```bash
# SSH into server
ssh user@your-server-ip

# Install Python
sudo apt update
sudo apt install python3-pip python3-venv

# Clone repo
git clone https://github.com/tientruongminh/CF_Tien23280088_Hoang23280060.git
cd CF_Tien23280088_Hoang23280060
git checkout multi-alpha-final
```

#### Step 2: Install Dependencies

```bash
cd project/ticket_selection/MultiAlphaProject
pip3 install -r /home/tiencd123456/CF_Tien23280088_Hoang23280060-1/requirements.txt
```

#### Step 3: Run with systemd (Auto-restart)

Create service file: `/etc/systemd/system/multi-alpha.service`

```ini
[Unit]
Description=Multi-Alpha Dashboard
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/CF_Tien23280088_Hoang23280060-1/project/ticket_selection/MultiAlphaProject
ExecStart=/usr/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable multi-alpha
sudo systemctl start multi-alpha
```

**Check status:**
```bash
sudo systemctl status multi-alpha
```

#### Step 4: Setup Nginx Reverse Proxy

Install Nginx:
```bash
sudo apt install nginx
```

Create config: `/etc/nginx/sites-available/multi-alpha`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable:**
```bash
sudo ln -s /etc/nginx/sites-available/multi-alpha /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: Setup SSL (HTTPS)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Access at:** `https://your-domain.com`

---

### 3B: Docker Deployment

#### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY project/ticket_selection/MultiAlphaProject/ ./
COPY project/apply_strategy/ ../apply_strategy/

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Build & Run

```bash
# Build
docker build -t multi-alpha-dashboard .

# Run
docker run -d -p 8501:8501 --name multi-alpha multi-alpha-dashboard

# Access at localhost:8501
```

#### Deploy to Cloud

**Google Cloud Run:**
```bash
gcloud run deploy multi-alpha \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**AWS ECS:** Similar process with ECR & ECS

---

## 📊 COMPARISON TABLE

| Feature | Local | Streamlit Cloud | Custom Server |
|---------|-------|-----------------|---------------|
| **Cost** | Free | Free (with limits) | $5-50/month |
| **Setup Time** | 5 min | 10 min | 30-60 min |
| **Public Access** | ❌ | ✅ | ✅ |
| **Always On** | ❌ | ⚠️ (sleeps) | ✅ |
| **Custom Domain** | ❌ | ⚠️ (premium) | ✅ |
| **Resource Limits** | Your PC | 1GB RAM | Unlimited |
| **Auto-deploy** | ❌ | ✅ (GitHub) | ⚠️ (manual) |

---

## 🎯 RECOMMENDATION BY USE CASE

### For Testing / Personal Use
→ **Option 1: Local** (simplest)

### For Sharing with Team / Portfolio
→ **Option 2: Streamlit Cloud** (free, easy)

### For Production Trading / Always-On
→ **Option 3: Custom Server** (reliable, scalable)

---

## 🔧 OPTIMIZATION TIPS

### Reduce App Size (for Cloud)

```bash
# Remove large backup folders before deploy
cd project/apply_strategy
rm -rf *_BACKUP_* *_OLD_*

# Keep only:
# - MultiAlpha_Results_Scenario1
# - MultiAlpha_Results_Scenario2
# - MultiAlpha_Results_Scenario3
# - FINAL_COMPARISON.md
```

### Add .gitignore

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environments
venv/
env/
ENV/

# Streamlit
.streamlit/secrets.toml

# Data (if too large)
# project/apply_strategy/MultiAlpha_Results*/

# Logs
*.log
```

### Reduce Data Files

If results too large (> 100MB):
```python
# In app.py, sample data for cloud
if os.environ.get('STREAMLIT_CLOUD'):
    # Load smaller dataset
    df = df.tail(1000)  # Last 1000 rows only
```

---

## 🚨 IMPORTANT NOTES

### Security

**1. Don't commit API keys**
- Use Streamlit secrets
- Or environment variables

**2. Protect sensitive data**
```python
# In app.py
if st.secrets.get("password"):
    password = st.text_input("Password", type="password")
    if password != st.secrets["password"]:
        st.stop()
```

### Performance

**1. Cache expensive operations**
```python
@st.cache_data
def load_data(path):
    return pd.read_csv(path)
```

**2. Lazy loading**
```python
# Only load when tab selected
with tabs[0]:
    if st.button("Load Heavy Data"):
        data = expensive_operation()
```

---

## ✅ DEPLOYMENT CHECKLIST

Before deploying:

- [ ] requirements.txt is complete
- [ ] All file paths are relative (not absolute)
- [ ] Large files removed or compressed
- [ ] API keys in secrets (not code)
- [ ] Test locally first
- [ ] README has deployment instructions
- [ ] .gitignore configured

---

## 🔗 QUICK LINKS

**Streamlit Cloud:** https://streamlit.io/cloud  
**Streamlit Docs:** https://docs.streamlit.io/deploy  
**Docker Hub:** https://hub.docker.com/  
**DigitalOcean:** https://www.digitalocean.com/  
**Render:** https://render.com/ (alternative to Streamlit Cloud)

---

## 🆘 TROUBLESHOOTING

### "Module not found" error
```bash
# Add to requirements.txt
echo "missing-package>=1.0.0" >> requirements.txt
```

### App won't start
```bash
# Check logs
streamlit run app.py --logger.level=debug
```

### Slow loading
```python
# Add caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_heavy_data():
    ...
```

### Out of memory
- Reduce data size
- Use cloud with more RAM
- Implement pagination

---

**Choose your deployment option and follow the steps above!**

For most users: **Start with Streamlit Cloud** (Option 2) - it's free and easiest to share.
