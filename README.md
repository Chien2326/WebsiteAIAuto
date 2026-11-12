# WebAiAuto

The web interface is a React single-page application. FastAPI serves its production build and provides the authentication and admin APIs.
Use Node.js 22 LTS for frontend development and production builds.

## Local development

1. In one PowerShell window, start FastAPI from the project root:

   ```powershell
   venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

2. In another PowerShell window, start Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. Open the Vite URL shown in the terminal (normally `http://localhost:5173`). Vite proxies `/api` requests to FastAPI on port 8000.

## Production / single-server mode

Build React, then start FastAPI:

```powershell
cd frontend
npm install
npm run build
cd ..
venv\Scripts\python.exe -m uvicorn app.main:app
```

FastAPI serves the React app and hashed assets from `frontend/dist`. Configure PostgreSQL and the application secrets in `.env` before enabling registration or deploying.

Initialize PostgreSQL with the schema in `database.txt`. Successful image, video,
and website generations are recorded in `ai_generations`; their output metadata
and relative file paths are stored in `generation_assets`. The generated files
are kept under the project `storage/generations` directory, while PostgreSQL
stores the generation records and asset references. Keep `storage/` on persistent
disk and include it in backups. Generation endpoints return an authenticated
asset URL; only the owning user can retrieve a saved result.

The public contact form submits to `POST /api/contact` and stores messages in
the PostgreSQL `contact_messages` table. Fresh databases receive this table from
`database.txt`; add its table and index statements to an existing database
before enabling the form. Messages are stored for follow-up and are not emailed
automatically.

## Pollinations image generation

1. Create a secret API key at [Pollinations](https://enter.pollinations.ai/keys).
2. Set `POLLINATIONS_API_KEY` in the server's `.env` file and restart FastAPI. Keep this key on the server; do not put it in frontend environment variables or commit it.
3. Sign in, open **Tạo ảnh**, enter a prompt, choose a style, aspect ratio, and number of images, then select **Tạo hình ảnh**.

The image endpoint uses Pollinations' `tongyi-mai/z-image-turbo` model by default. Override it with `POLLINATIONS_IMAGE_MODEL` if needed. Requests are sent through FastAPI, and generated images are saved with their prompt and settings before being returned to the browser for preview and download. Pollinations API key budgets and model pricing apply; check your key's permissions and Pollen balance in your Pollinations account.

The video studio uses the same server-side `POLLINATIONS_API_KEY` and Pollinations' `google/veo-3.1-fast` model by default. Set `POLLINATIONS_VIDEO_MODEL` to another video model available to your key if needed. Ensure the key permits the selected video model. Video generation can take longer and use more Pollen than image generation; the generated MP4 is saved and then streamed back to the browser for playback and download.

The website studio uses the same server-side `POLLINATIONS_API_KEY` and the Pollinations chat-completions API to generate structured landing-page copy. It uses `openai/gpt-5.4-nano` by default; override it with `POLLINATIONS_TEXT_MODEL` if needed. The generated JSON is validated by FastAPI, saved as a generation asset, and rendered as text in the existing React preview. Generated HTML, CSS, and JavaScript are not executed. Choose a website type, palette, and language, describe the site, then select **Tạo website**. Requests may consume Pollen according to your selected model and key budget.

The public pricing page at `/pricing` currently displays editable sample prices and lets visitors select a plan before continuing to registration or contact. Payment processing and paid-plan entitlements are not implemented; confirm all prices and plan benefits before publishing them as offers.

## Credits

Every generation is charged in credits, priced on the server in `app/core/credits.py`:

| Generation | Cost |
|---|---|
| Image | 1 credit per image (1–4 per request) |
| Video | 2 credits per second (5 s = 10, 10 s = 20) |
| Website | 2 credits |

New accounts start with 10 credits (the `users.credits_balance` default, recorded
in the ledger by the signup trigger). A request is charged before the provider is
called and refunded automatically if the provider fails or the result cannot be
saved. When only some images in a request succeed, the unused credits are
refunded. Each charge and refund is a row in `credit_transactions`, so
`SELECT * FROM v_credit_balance_mismatch` must stay empty.

A user can have at most 3 generations in progress, and at most 1 video.
Generations still `processing` after 15 minutes (for example after a server
restart) are marked `failed` and refunded by a background task that runs every
5 minutes.

## Rate limits

Login, registration, the contact form, and generation requests are rate-limited
per IP address or per user. The counters are kept in memory per process; use a
shared store such as Redis before running several workers. Behind a reverse
proxy, start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy IP>` so
limits apply to visitors' real addresses rather than to the proxy.

## Tests

```powershell
venv\Scripts\python.exe -m unittest discover -s tests
```
# WebsiteAIAuto
