# BabbelClone — Frontend

This folder contains a minimal Vite + React + TypeScript scaffold for day one frontend work.

Quick start:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

What's included:
- Vite with React plugin
- TypeScript
- Basic routing (`/`)
- Placeholder chat UI under `src/components/ChatSkeleton.tsx`

Backend wiring:
- The frontend reads backend URLs from env: `VITE_BACKEND_HTTP` and `VITE_BACKEND_WS`.
- A local example env is provided in `.env.development` which points to `http://localhost:3000`.

Run frontend + backend locally:

```bash
# in one terminal: start the backend
cd backend
npm install
node server.js

# in another terminal: start the frontend (will pick up .env.development)
cd frontend
npm install
npm run dev

# open http://localhost:5173 (or the port Vite shows)
```

Quick verify steps (server persistence):

1. With the backend running, broadcast a test message via WebSocket:

```bash
cd backend
node -e "const WebSocket=require('ws'); const ws=new WebSocket('ws://localhost:3000/ws'); ws.on('open',()=>{ws.send(JSON.stringify({author:'test',text:'hello via ws'})); ws.close();});"
```

2. Confirm the message was persisted by fetching history:

```bash
curl http://localhost:3000/messages | jq .
```

The frontend will fetch `/messages` on load and subscribe to the WS at the URL from env; open the app to see messages in the UI.

E2E tests (Playwright)
-----------------------
This project includes a minimal Playwright setup that runs the dev server and executes tests.

Install dev deps and browsers:

```bash
cd frontend
npm install
npx playwright install --with-deps
```

Run the tests:

```bash
cd frontend
npx playwright test
```

The included test uses `localStorage` to inject messages so it does not require a backend.

---

## Lesson Mock API

The lesson cards are loaded from a local mock JSON file:
- `src/mocks/lessonCards.json`

This allows you to test the lesson flow without a backend. To update lesson content, edit this file.

## Running the Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev
   ```
3. Open the URL shown in the terminal (usually http://localhost:5173 or higher).

## Testing (Playwright E2E)

To run end-to-end tests:
```bash
cd frontend
npx playwright test
```

Tests are located in `src/tests/`. Make sure the dev server is running before executing tests.

## Folder Structure
- `src/pages/DayTwo.tsx`: Main lesson flow
- `src/components/ImmersiveCard.tsx`: Card UI, animation, audio
- `src/mocks/lessonCards.json`: Mock lesson data

## Notes
- The chat UI is hidden by default.
- Backend integration is planned; for now, all lesson data is local.

---
