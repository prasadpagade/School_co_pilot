# 📱 Testing on iPhone - Quick Guide

## Step 1: Find Your Computer's IP Address

Run this command in your terminal:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Or on macOS, you can also:
1. System Preferences → Network
2. Select your active connection (Wi-Fi or Ethernet)
3. Note the IP address (e.g., `192.168.1.100`)

## Step 2: Start Server on Network Interface

The server needs to bind to `0.0.0.0` (all interfaces) instead of `127.0.0.1` (localhost only).

**Stop your current server** (Ctrl+C) and restart with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

This makes the server accessible from your local network.

## Step 3: Connect iPhone to Same Network

- Make sure your iPhone is on the **same Wi-Fi network** as your computer
- Both devices must be on the same network (e.g., same router)

## Step 4: Access from iPhone

1. Open Safari on your iPhone
2. Type in the address bar:
   ```
   http://YOUR_IP_ADDRESS:8000
   ```
   Replace `YOUR_IP_ADDRESS` with the IP from Step 1
   
   Example: `http://192.168.1.100:8000`

3. The app should load!

## Troubleshooting

### Can't Connect?

1. **Check Firewall**:
   - macOS: System Preferences → Security & Privacy → Firewall
   - Temporarily disable or allow Python/uvicorn

2. **Check IP Address**:
   - Make sure you're using the correct IP (Wi-Fi IP, not Ethernet)
   - Try `ipconfig getifaddr en0` for Wi-Fi IP on macOS

3. **Check Network**:
   - Both devices on same Wi-Fi?
   - Try pinging from iPhone: Open terminal app, ping your computer's IP

4. **Port Already in Use?**:
   - Change port: `--port 8001`
   - Update URL on iPhone accordingly

### CORS Errors?

The app is configured to allow all origins in development, so this shouldn't be an issue.

### Mobile UI Not Working?

- Clear Safari cache: Settings → Safari → Clear History and Website Data
- Try in Chrome on iPhone if Safari has issues
- Check that viewport meta tag is present (it is!)

## Quick Test Checklist

- [ ] Server running on `0.0.0.0:8000`
- [ ] iPhone on same Wi-Fi network
- [ ] Can access `http://YOUR_IP:8000` from iPhone
- [ ] Test chat functionality
- [ ] Test voice input
- [ ] Test image upload
- [ ] Test calendar features
- [ ] Test all tabs

## Alternative: Use ngrok (For Testing Outside Network)

If you want to test from anywhere (not just same network):

1. **Install ngrok**:
   ```bash
   brew install ngrok
   # Or download from https://ngrok.com
   ```

2. **Start your server** (on localhost):
   ```bash
   uvicorn app.main:app --reload
   ```

3. **In another terminal, start ngrok**:
   ```bash
   ngrok http 8000
   ```

4. **Use the ngrok URL** on your iPhone:
   - ngrok will show a URL like `https://abc123.ngrok.io`
   - Use this URL on your iPhone
   - Works from anywhere!

## Pro Tips

- **Bookmark the URL** on your iPhone for easy access
- **Add to Home Screen**: Safari → Share → Add to Home Screen (feels like a native app!)
- **Use HTTPS in production** for better security and PWA features

