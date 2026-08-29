# MedAssistAI

One-page Streamlit medical laboratory report workspace.

## Main flow
Login → Home → Upload image/PDF → Gemini extraction → Outcome table → Dashboard → AI Insights → Urdu dietary section → Settings.

## Setup
1. Create/activate your environment.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Gemini API key, or use `.streamlit/secrets.toml`.
4. Run `streamlit run app.py`.

The included project archive intentionally does not contain API keys, service-account private keys, the SQLite database, or uploaded medical images.
