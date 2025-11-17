# Streamlit Cloud Deployment Guide

## Automatic Database Setup

The app automatically initializes the database on startup:
1. Creates SQLite database with schema
2. Seeds JEE syllabus topics (62 topics across Physics, Chemistry, Math)

This happens automatically - no manual setup needed!

## Deployment Steps

### 1. Configure Secrets on Streamlit Cloud

In your Streamlit Cloud dashboard, add these secrets:

```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
```

### 2. Deploy

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Select `app.py` as the main file
5. Add your Gemini API key in Secrets
6. Deploy!

## Database Persistence

⚠️ **Important:** On Streamlit Cloud, the database resets on each deployment or when the app goes to sleep after inactivity.

**For production use, consider:**
- Using Streamlit Cloud's file upload for data persistence
- Migrating to a persistent database (PostgreSQL, MySQL)
- Using cloud storage (AWS S3, Google Cloud Storage)

## Environment Variables

The app uses these environment variables:
- `GEMINI_API_KEY` (required) - Your Google Gemini API key

## Testing Locally

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
echo "GEMINI_API_KEY=your-key-here" > .env

# 4. Run the app
streamlit run app.py
```

The database will be automatically created in `mindmentor.db` on first run.

## Troubleshooting

### "Database initialization error"
- Check that `src/data/schema.sql` exists
- Verify file permissions
- Check logs for specific error messages

### "No topics found"
- The seeding process may have failed
- Check Streamlit Cloud logs
- Ensure the app has write permissions

### "API key not found"
- Ensure you've added `GEMINI_API_KEY` to Streamlit Cloud secrets
- For local development, check your `.env` file
