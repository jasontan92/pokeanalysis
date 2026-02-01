# Deploy to Google Cloud

## Option 1: Compute Engine VM (Recommended - Simplest)

### Step 1: Create a VM
```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Create a small VM (about $5/month)
gcloud compute instances create pokemon-monitor \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud
```

### Step 2: SSH into the VM
```bash
gcloud compute ssh pokemon-monitor --zone=us-central1-a
```

### Step 3: Install dependencies on VM
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### Step 4: Clone/upload your code
```bash
# Option A: Clone from GitHub (if you push it there)
git clone https://github.com/YOUR_USERNAME/pokeanalysis.git
cd pokeanalysis

# Option B: Upload files using gcloud
# (Run this from your local machine)
# gcloud compute scp --recurse ./pokeanalysis pokemon-monitor:~/ --zone=us-central1-a
```

### Step 5: Set up the project
```bash
cd pokeanalysis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with your credentials
nano .env
# Paste your Telegram credentials and save (Ctrl+X, Y, Enter)
```

### Step 6: Test the monitor
```bash
python monitor.py
```

### Step 7: Set up cron job
```bash
# Open crontab editor
crontab -e

# Add this line (runs every 30 minutes):
*/30 * * * * cd /home/$USER/pokeanalysis && /home/$USER/pokeanalysis/venv/bin/python monitor.py >> /home/$USER/pokeanalysis/data/monitor.log 2>&1

# Save and exit
```

### Step 8: Verify cron is running
```bash
# Check cron logs
grep CRON /var/log/syslog

# Or tail your monitor log
tail -f ~/pokeanalysis/data/monitor.log
```

---

## Your .env file contents:
```
TELEGRAM_BOT_TOKEN=8516082435:AAEusJe6vQHqkluS7jLgMgBD4m9PUKx2a0k
TELEGRAM_CHAT_ID=6076213196
SEARCH_TERM=1996 no rarity
```

---

## Useful Commands

```bash
# Check if monitor is running
ps aux | grep monitor

# View recent logs
tail -50 ~/pokeanalysis/data/monitor.log

# Stop the cron job (edit and remove the line)
crontab -e

# Restart after code changes
cd ~/pokeanalysis && git pull  # if using git
```

---

## Cost Estimate
- e2-micro VM: ~$5-7/month (or FREE under Google Cloud free tier)
- The free tier includes 1 e2-micro instance per month
