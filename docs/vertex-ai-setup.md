# Using Vertex AI instead of an AI Studio key

The labeling notebooks can call Gemini in two ways:

| Backend | When to use it | What you need |
|---|---|---|
| **AI Studio** (default) | Quick start, small runs | `GEMINI_API_KEY` in `.env` |
| **Vertex AI** | Billed through Google Cloud, better for the full 7,363-review run | A Google Cloud project with billing and the Vertex AI API enabled |

Nothing in the code changes. A switch in `.env` decides which one is used.
(The code that reads it is the client setup cell in `notebooks/scale_up.ipynb` and `notebooks/harm_recheck.ipynb`.)

## One-time setup

1. **Pick or create a Google Cloud project** at [console.cloud.google.com](https://console.cloud.google.com) and make sure **billing** is linked to it. Write down the project ID (not the display name).
2. **Enable the Vertex AI API** on that project: in the console search for "Vertex AI API" and click **Enable**, or run
   ```bash
   gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
   ```
3. **Install the gcloud CLI** if you do not have it: [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).
4. **Sign in so Python can use your credentials:**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```
   A browser window opens. Use the Google account that has access to the project.

## Turn it on

Copy `.env.example` to `.env` in the repository root (if you have not yet), then edit `.env`:

```bash
USE_VERTEX=1
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
```

`GEMINI_API_KEY` is not needed while `USE_VERTEX=1`. To go back to AI Studio, delete the `USE_VERTEX` line (or comment it out) and keep `GEMINI_API_KEY`.

Restart the notebook kernel after changing `.env`, then run the setup cells from the top. The progress panel in the labeling run prints which backend it is using ("Vertex AI" or "AI Studio").

## If something fails

- **`403` or "API has not been used":** the Vertex AI API is not enabled on that project yet (step 2), or it was enabled a minute ago and needs a moment.
- **"Could not automatically determine credentials":** run `gcloud auth application-default login` again.
- **`429`, `500`, `503`, `504`:** temporary Google errors. The labeling code retries these automatically and keeps every finished label, so just run the cell again.
- **Wrong project billed:** check `GOOGLE_CLOUD_PROJECT` in `.env`, then restart the kernel.

## Safety

`.env` is ignored by git. Never commit it, and never paste a key or project credentials into a notebook, an issue or a pull request.
