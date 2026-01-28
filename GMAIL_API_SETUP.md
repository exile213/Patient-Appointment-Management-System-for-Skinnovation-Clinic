# Gmail API Setup Guide for Skinnovation Beauty Clinic

This guide will help you set up Gmail API credentials to send emails from your Django application.

## Prerequisites

- A Google Account (Gmail)
- Access to Google Cloud Console
- The email address you want to send emails from

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top and select **"New Project"**
3. Enter project name: `Skinnovation-Email-Service`
4. Click **"Create"**

## Step 2: Enable Gmail API

1. In the Google Cloud Console, go to **"APIs & Services" > "Library"**
2. Search for **"Gmail API"**
3. Click on **Gmail API** and then click **"Enable"**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials" > "OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - Choose **"External"** user type
   - Fill in app name: `Skinnovation Beauty Clinic`
   - Add your email as support and developer email
   - Skip optional fields and click **"Save and Continue"**
   - Add scope: `https://www.googleapis.com/auth/gmail.send`
   - Click **"Save and Continue"** through the remaining steps

4. Back at "Create OAuth client ID":
   - Application type: **"Web application"**
   - Name: `Skinnovation Email Client`
   - Authorized redirect URIs: `http://localhost:8080/`
   - Click **"Create"**

5. **SAVE THESE VALUES:**
   - `Client ID` (looks like: `xxxxx.apps.googleusercontent.com`)
   - `Client Secret` (random string)

## Step 4: Get Refresh Token

You need to run a one-time authorization flow to get a refresh token. Save this Python script as `get_refresh_token.py`:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# The scopes required for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_refresh_token(client_id, client_secret):
    """Get refresh token using OAuth2 flow"""
    
    # Create OAuth2 credentials
    credentials_info = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }
    
    # Save to temporary file
    with open('client_secret.json', 'w') as f:
        json.dump(credentials_info, f)
    
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES
    )
    
    credentials = flow.run_local_server(port=8080)
    
    print("\n" + "="*50)
    print("SUCCESS! Here are your credentials:")
    print("="*50)
    print(f"GMAIL_CLIENT_ID={client_id}")
    print(f"GMAIL_CLIENT_SECRET={client_secret}")
    print(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}")
    print(f"GMAIL_SENDER_EMAIL=<your-gmail-address>")
    print("="*50)
    print("\nAdd these to your Render environment variables!")
    
    return credentials.refresh_token


if __name__ == '__main__':
    print("Gmail API Refresh Token Generator")
    print("="*50)
    
    # Input credentials from Step 3
    client_id = input("Enter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()
    
    # Get refresh token
    refresh_token = get_refresh_token(client_id, client_secret)
```

**Run the script:**

```bash
# Install required package
pip install google-auth-oauthlib

# Run the script
python get_refresh_token.py
```

**What happens:**
1. Enter your Client ID and Client Secret when prompted
2. Your browser will open asking you to sign in with Google
3. Sign in with the Gmail account you want to send emails from
4. Grant permissions when asked
5. The script will print your credentials

**COPY THE OUTPUT** - you'll need these values for Render!

## Step 5: Configure Environment Variables on Render

1. Go to your Render dashboard
2. Select your `skinnovation-clinic` web service
3. Click **"Environment"** tab
4. Add these environment variables (use values from Step 4):

```
GMAIL_CLIENT_ID=<your-client-id>
GMAIL_CLIENT_SECRET=<your-client-secret>
GMAIL_REFRESH_TOKEN=<your-refresh-token>
GMAIL_SENDER_EMAIL=<your-gmail-address>
```

**Example:**
```
GMAIL_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ
GMAIL_REFRESH_TOKEN=1//0abcdefghijklmnopqrstuvwxyz...
GMAIL_SENDER_EMAIL=noreply@yourdomain.com
```

5. Click **"Save Changes"**

## Step 6: Remove Old Email Environment Variables

**Optional but recommended:** Remove these old variables to clean up:
- `MAILJET_API_KEY`
- `MAILJET_API_SECRET`
- `MAILJET_SENDER_EMAIL`
- `MAILJET_SENDER_NAME`
- `MAILTRAP_API_TOKEN`

## Step 7: Deploy and Test

1. **Commit and push your code changes**:
   ```bash
   git add .
   git commit -m "Migrate from Mailjet/Mailtrap to Gmail API"
   git push origin main
   ```

2. Render will automatically redeploy your application

3. **Test the email functionality:**
   - Try the password reset feature
   - Register a new user and check for welcome email
   - Visit the test email page if available

## Troubleshooting

### "Invalid grant" error
- The refresh token may have expired
- Re-run the `get_refresh_token.py` script
- Make sure you're using the same Google account

### Emails not sending
- Check Render logs for error messages
- Verify all 4 environment variables are set correctly
- Make sure Gmail API is enabled in Google Cloud Console
- Verify the Gmail account has access (check OAuth consent screen)

### "Access token expired"
- This is normal - the library automatically refreshes using the refresh token
- If it persists, regenerate the refresh token

## Security Notes

- **Never commit credentials to Git**
- Keep your `client_secret` secure
- The refresh token provides ongoing access - protect it
- Consider using a dedicated Google Workspace account for production
- Regularly review OAuth consent screen authorized apps

## Gmail Sending Limits

- **Personal Gmail**: ~500 emails/day
- **Google Workspace**: ~2,000 emails/day

If you need higher limits, consider:
- Using a transactional email service (SendGrid, AWS SES)
- Getting a Google Workspace account
- Implementing email queuing

## Need Help?

If you encounter issues:
1. Check the Render logs for specific error messages
2. Verify all environment variables are set correctly
3. Test locally first before deploying to Render
4. Review Google Cloud Console audit logs
