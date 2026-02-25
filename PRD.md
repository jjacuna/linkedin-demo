# LinkedIn Post Generator — Product Requirements Document

## Context
Build a Mac-style single-page web app that takes a business persona + content idea, sends them to Gemini 2.5 Flash via OpenRouter to generate a LinkedIn post and an image prompt, then calls the Nano Banana API to generate an image — all copyable/downloadable with regeneration support.

---

## Inputs

### 1. Business / Persona Box (required, persistent via localStorage)
- **Who they are** — name, title, industry
- **What they do** — business description / value prop
- **Call to action** — what they want readers to do (book a call, visit site, etc.)
- Auto-saved to localStorage on change; auto-fills on next visit
- Collapsible card with "Edit" / "Clear" buttons once saved

### 2. Content Idea Box (required)
- Free-form textarea — can be a sentence, bullet points, or a full article paste
- Character cap: **10,000 characters** (≈2,500 words)
- Live character count displayed below the field

---

## Processing

### Step 1: AI Text Generation — OpenRouter → Gemini 2.5 Flash
- Single API call with a system prompt that:
  1. Summarizes / distills the content idea
  2. Writes a LinkedIn post (hook, body, CTA) in the persona's voice
  3. Generates an image prompt for Nano Banana (1:1 square format, professional/engaging style)
- Returns structured JSON: `{ "post": "...", "imagePrompt": "..." }`

### Step 2: Image Generation — Nano Banana API
- Takes the image prompt from Step 1
- Calls Nano Banana REST API with API key auth
- Generates a **1:1 square image** (1080×1080) optimized for LinkedIn feed posts
- Returns image URL or binary

---

## Outputs (displayed below the form)

### Generated Post Card
- Rendered in a styled card with the LinkedIn post text
- **Copy Text** button → copies plain text to clipboard with toast confirmation
- Character count shown (LinkedIn limit: 3,000 chars)

### Generated Image Card
- Image displayed as a preview (1:1 square)
- **Download** button → saves PNG/JPG locally
- **Copy Image** button → copies image to clipboard
- **Regenerate Image** button → re-calls Nano Banana with current prompt

### Image Prompt Editor
- Editable textarea showing the AI-generated image prompt
- User can tweak the prompt, then hit **Regenerate Image** to get a new image
- Sits directly above the image preview for easy edit→regenerate flow

---

## UI / UX

### Design Language
- macOS-inspired: frosted glass panels (`backdrop-filter: blur`), soft shadows, rounded corners (12-16px), system font stack (-apple-system, SF Pro)
- Light mode, clean whites (#FAFAFA background) and soft grays
- Accent color: LinkedIn blue (#0A66C2) for primary actions
- Single-page layout, no navigation

### Layout (top to bottom)
```
┌─────────────────────────────────────────────┐
│  LinkedIn Post Generator          [header]  │
├──────────────────────┬──────────────────────┤
│  Business / Persona  │  Content Idea        │
│  (collapsible)       │  (textarea + count)  │
│                      │                      │
├──────────────────────┴──────────────────────┤
│            [ ✦ Generate Post ]              │
├──────────────────────┬──────────────────────┤
│  LinkedIn Post       │  Image Preview       │
│  (text + copy btn)   │  (img + download +   │
│                      │   copy + regenerate) │
│                      ├──────────────────────┤
│                      │  Image Prompt        │
│                      │  (editable textarea) │
└──────────────────────┴──────────────────────┘
```

### Interactions
- **Generate** button disabled until both persona + content idea have content
- Loading: skeleton shimmer on output cards during API calls
- Toast notifications (bottom-right) for copy/download success
- Responsive but optimized for desktop (1200px+ primary target)

---

## Tech Stack
- **Frontend**: HTML + Tailwind CSS (CDN) + vanilla JS
- **Backend**: Python Flask
- **AI**: OpenRouter API → `google/gemini-2.5-flash`
- **Image**: Nano Banana REST API (API key auth)
- **Environment**: `.env` for all secrets

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Serve the main page |
| POST | `/generate` | Takes persona + content idea, calls OpenRouter, returns post text + image prompt, then calls Nano Banana and returns image URL |
| POST | `/regenerate-image` | Takes an image prompt, calls Nano Banana, returns new image URL |

---

## Files to Create

| File | Purpose |
|------|---------|
| `app.py` | Flask server — routes, OpenRouter + Nano Banana API calls |
| `templates/index.html` | Full UI — HTML + Tailwind CDN + inline JS |
| `.env.example` | Template: `OPENROUTER_API_KEY=`, `NANO_BANANA_API_KEY=` |
| `requirements.txt` | `flask`, `requests`, `python-dotenv` |
| `PRD.md` | This document saved in the project for reference |

---

## Environment Variables
```
OPENROUTER_API_KEY=your-openrouter-key
NANO_BANANA_API_KEY=your-nano-banana-key
```

---

## Build Steps
1. Create project structure and install dependencies
2. Build Flask backend with `/generate` and `/regenerate-image` routes
3. Build the full UI in `templates/index.html` (macOS style, Tailwind)
4. Wire up frontend JS to call backend APIs and render results
5. Add localStorage persistence for persona fields
6. Add copy/download/regenerate interactions
7. Test end-to-end flow

---

## Verification
1. `pip install -r requirements.txt` → clean install
2. Copy `.env.example` to `.env`, add real API keys
3. `python app.py` → server starts on http://localhost:5000
4. Fill in persona + content idea → hit Generate
5. Confirm LinkedIn post text appears → Copy works
6. Confirm image renders → Download + Copy Image work
7. Edit image prompt → Regenerate → new image appears
8. Refresh page → persona fields auto-filled from localStorage
