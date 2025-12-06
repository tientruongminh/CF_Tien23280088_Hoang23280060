# Streamlit Cloud Deployment - Step by Step

## ✅ PREPARATION COMPLETE

**Config files created:**
- ✅ `.streamlit/config.toml` - Theme & server settings
- ✅ `.gitignore` - Exclude unnecessary files
- ✅ `requirements.txt` - Python dependencies

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Push Config to GitHub

```bash
cd /home/tiencd123456/CF_Tien23280088_Hoang23280060-1

# Add new files
git add .streamlit/config.toml requirements.txt

# Commit
git commit -m "feat: Add Streamlit Cloud configuration"

# Push to branch
git push origin multi-alpha-final
```

### Step 2: Go to Streamlit Cloud

**Open:** https://share.streamlit.io/

**Sign In:**
- Click "Sign in with GitHub"
- Authorize Streamlit

### Step 3: Create New App

1. Click **"New app"** button (top right)

2. Fill in details:
   ```
   Repository: tientruongminh/CF_Tien23280088_Hoang23280060
   Branch: multi-alpha-final
   Main file path: project/ticket_selection/MultiAlphaProject/app.py
   ```

3. Click **"Deploy!"**

### Step 4: Wait for Deployment

- ⏳ Takes 2-5 minutes
- You'll see build logs
- Status: "Building" → "Running"

### Step 5: Get Your URL

**Your app will be live at:**
```
https://cf-tien-hoang-multi-alpha.streamlit.app
```
(Exact URL shown after deployment)

---

## 🔧 OPTIONAL: Configure Secrets (for Gemini AI)

If you want AI chat to work for visitors:

1. In Streamlit dashboard → Your app → ⚙️ Settings
2. Click **"Secrets"**
3. Add:
```toml
[gemini]
api_key = "your-gemini-api-key-here"
```
4. Save

Then update `chat_assistant.py` to use secrets:
```python
# Add at top of file
import streamlit as st

# Replace API key input with:
if "gemini" in st.secrets:
    api_key = st.secrets["gemini"]["api_key"]
else:
    api_key = st.text_input("Gemini API Key", type="password")
```

---

## 📊 WHAT VISITORS WILL SEE

✅ **Tab 1: Model Evaluation** - Grade A, metrics  
✅ **Tab 2: Portfolio Performance** - Charts, results  
✅ **Tab 3: Signal Analysis** - Per-stock breakdown  
✅ **Tab 4: AI Assistant** - Gemini chat (if configured)  
✅ **Sidebar:** 3 scenario selector  

---

## 🎯 SHARE YOUR APP

Once deployed, share the URL with:
- Team members
- Investors
- Portfolio managers
- Anyone with the link!

**Public access** - no login required (unless you add authentication)

---

## 🔒 OPTIONAL: Add Password Protection

To restrict access, add to `app.py` (top of main function):

```python
def main():
    # Password protection
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("Enter Password", type="password")
        if st.button("Login"):
            if password == st.secrets.get("app_password", "your-secret-password"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
                st.stop()
        st.stop()
    
    # Rest of your app code...
```

Then add to Secrets:
```toml
app_password = "your-secure-password-123"
```

---

## ⚠️ IMPORTANT NOTES

### Resource Limits (Free Tier)

- **RAM:** 1 GB
- **CPU:** Shared
- **Sleep:** After 7 days of inactivity

**If app is slow:**
- Data is large (25MB results)
- Consider reducing data size
- Or upgrade to Streamlit paid plan

### Auto-Updates

**Every push to `multi-alpha-final` branch automatically updates the app!**

No need to manually redeploy.

---

## 🐛 TROUBLESHOOTING

### "Requirements file not found"

Add to root directory:
```bash
cp requirements.txt /home/tiencd123456/CF_Tien23280088_Hoang23280060-1/
git add requirements.txt
git commit -m "Add requirements.txt to root"
git push
```

### "Module import error"

Check all imports use relative paths:
```python
# Good ✅
from alphas import calculate_mr_score

# Bad ❌
from /home/tiencd123456/.../alphas import calculate_mr_score
```

### "File not found"

All paths must be relative to app.py:
```python
# Good ✅
results_dir = '../../../apply_strategy/MultiAlpha_Results'

# Already correct in your app.py ✅
```

### App won't wake from sleep

Free tier sleeps after inactivity. Solutions:
1. Visit URL to wake it up
2. Upgrade to paid plan ($20/month for always-on)
3. Use uptime monitoring (e.g., UptimeRobot)

---

## ✅ DEPLOYMENT CHECKLIST

Before clicking "Deploy":

- [x] Config files created (`.streamlit/config.toml`)
- [x] Dependencies listed (`requirements.txt`)
- [ ] Push to GitHub (`git push origin multi-alpha-final`)
- [ ] Sign up for Streamlit Cloud
- [ ] Create new app
- [ ] Wait 2-5 minutes
- [ ] Test app works
- [ ] Share URL with team!

---

## 🎉 SUCCESS!

Once deployed:
1. ✅ App is live 24/7 (with sleep after inactivity)
2. ✅ Public URL to share
3. ✅ Auto-updates from GitHub
4. ✅ Professional dashboard accessible worldwide

**Your Multi-Alpha strategy is now online!** 🚀

---

*Need help? Check Streamlit docs: https://docs.streamlit.io/deploy*
