# LingoVision (BabbleClone)

### A Visual-First Language Learning MVP

> Learn Spanish through images and sounds — no translations, just pure immersion

**Complete a full vocabulary lesson with 11 immersive flashcards**

[Features](#features) · [Tech Stack](#tech-stack) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API Docs](#api-documentation) · [Team](#team)

---

## Application Preview

The application features a clean, immersive learning interface:

- **Splash Screen**: Welcome page with audio unlock ("Start Unit" button)
- **Home Dashboard**: Lesson catalog with unit descriptions
- **Immersive Cards**: Full-screen image + audio, 2-second thinking gap, then Spanish word reveal
- **Linear Navigation**: Next/Back card progression through the lesson

---

## Features

### Visual-First Deciphering Engine
- **The "Thinking Gap"**: Users see an image and hear audio, then wait 2 seconds before the Spanish word appears
- **No Translation Crutch**: Forces the brain to create direct neural links between concepts and sounds
- **3 Card Types**: Immersive (image + audio to word), Drill (with English bridge), Concept (grammar notes)

### Audio-Visual Learning Flow
- Browser autoplay unlock via Splash Screen interaction
- Howler.js audio engine for reliable cross-browser playback
- High-quality images paired with native pronunciation

### REST API Backend
- Two clean endpoints serving lesson data from Supabase (PostgreSQL)
- LingoCard data model shared between frontend and backend
- Row Level Security for public read access — no auth overhead

### Modern UI/UX
- Responsive React frontend with Tailwind CSS
- Framer Motion animations for the "decoded" text reveal
- Zustand state management for lesson progression
- Mobile-friendly design

---

## Tech Stack

### Frontend (Michael)

| Technology | Purpose |
|-----------|---------|
| **React 17** + **Vite** | Fast development and HMR |
| **Tailwind CSS** | Utility-first responsive styling |
| **Framer Motion** | "Thinking Gap" fade-in animations |
| **Zustand** | Lightweight lesson state management |
| **Howler.js** | Cross-browser audio playback |
| **React Router** | SPA navigation (Splash, Home, Lesson) |

### Backend (Manuel)

| Technology | Purpose |
|-----------|---------|
| **Node.js** + **Express** | REST API server |
| **Supabase (PostgreSQL)** | Cloud database with instant REST |
| **Row Level Security** | Public read access, no auth needed |
| **dotenv** | Environment configuration |
| **CORS** | Cross-origin frontend access |

### DevOps & Testing

| Technology | Purpose |
|-----------|---------|
| **GitHub Actions** | CI/CD pipeline |
| **Playwright** | End-to-end browser testing |
| **nodemon** | Backend hot-reload in development |

---

## Architecture

```
┌─────────────────────┐
│   React Frontend    │  (Vite dev server)
│   Port: 5173        │
│   Splash → Home →   │
│   Lesson Cards      │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│   Express Backend   │  (Node.js)
│   Port: 3000        │
│   /api/units        │
│   /api/units/:id    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Supabase          │  (Cloud PostgreSQL)
│   units table       │
│   cards table       │
│   Row Level Security│
└─────────────────────┘
```

**Component Responsibilities:**
- **Frontend (React)**: User interface, lesson flow, audio playback, card animations
- **Backend (Express)**: REST API, database queries, data formatting
- **Database (Supabase)**: Persistent storage for units and cards with RLS policies

---

## Quick Start

### Prerequisites
- Node.js 18+
- Supabase account (free tier)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/OasisView/BabbleClone.git
cd BabbleClone
```

**2. Backend Setup**
```bash
cd backend
npm install
```

Create `backend/.env`:
```
PORT=3000
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**3. Database Setup**

In Supabase SQL Editor, run these files in order:
- `supabase/schema.sql` — creates units and cards tables with RLS
- `supabase/seed.sql` — inserts 11 Spanish vocabulary cards

**4. Frontend Setup**
```bash
cd frontend
npm install
```

### Running Locally

**Terminal 1 — Backend:**
```bash
cd backend
npm run dev
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

**Access the Application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:3000

---

## API Documentation

### List Units
```
GET /api/units
```
**Response:**
```json
{
  "units": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Vocabulary Lesson",
      "description": "Learning Spanish through Images",
      "language": "Spanish",
      "card_count": 11
    }
  ]
}
```

### Get Unit with Cards
```
GET /api/units/:id
```
**Response:**
```json
{
  "unit": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Vocabulary Lesson",
    "description": "Learning Spanish through Images",
    "language": "Spanish",
    "card_count": 11
  },
  "cards": [
    {
      "id": "1",
      "type": "immersive",
      "visual_url": "/images/GirlApple.png",
      "audio_url": "https://...",
      "target_text": "Manzana",
      "english_bridge": "Apple",
      "sentence": "Ella come una manzana en el parque."
    }
  ]
}
```

### Shared Data Model — LingoCard
```typescript
type LingoCard = {
  id: string;
  type: 'immersive' | 'drill' | 'concept';
  visual_url: string;
  audio_url: string;
  target_text: string;
  english_bridge?: string;
  grammar_note?: string;
  sentence?: string;
}
```

---

## Testing

### E2E Tests (Playwright)
```bash
cd frontend
npx playwright test
```

Tests cover:
- **Smoke test**: App loads with BabbelClone header
- **Navigation flow**: Splash → Home → Lesson (click-through)

### Backend API Testing
```bash
curl http://localhost:3000/api/units
curl http://localhost:3000/api/units/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Lesson Content

The demo unit includes **11 Spanish vocabulary cards**:

| # | Spanish | English | Image |
|---|---------|---------|-------|
| 1 | Manzana | Apple | GirlApple.png |
| 2 | Gato | Cat | CatSleeping.jpg |
| 3 | Libro | Book | reading-in-bed.jpg |
| 4 | Casa | House | House_with_small_garden.jpg |
| 5 | Agua | Water | WaterAfterRun.jpg |
| 6 | Flor | Flower | child-smelling-flowers.jpg |
| 7 | Sol | Sun | SunShineSummer.jpeg |
| 8 | Arbol | Tree | TreeUnderBlossoms.jpeg |
| 9 | Perro | Dog | ChildWithDog.jpg |
| 10 | Familia | Family | FamilyDinner.jpg |
| 11 | Cuidado | Watch out | SkiTrees.jpeg |

---

## Project Structure

```
BabbleClone/
├── backend/                 # Express API server
│   ├── server.js            # Main server with routes
│   ├── lib/supabase.js      # Supabase client
│   ├── package.json         # Backend dependencies
│   └── .env                 # Environment variables (gitignored)
├── frontend/                # React + Vite application
│   ├── src/
│   │   ├── pages/           # Splash, Home, DayTwo
│   │   ├── components/      # Header, ImmersiveCard, etc.
│   │   ├── store/           # Zustand lesson store
│   │   ├── mocks/           # Local lesson card data
│   │   └── types/           # LingoCard TypeScript type
│   ├── tests/               # Playwright E2E tests
│   └── package.json
├── supabase/
│   ├── schema.sql           # Database table definitions
│   └── seed.sql             # Demo lesson seed data
├── .github/workflows/       # CI/CD (Playwright E2E)
├── PRD.md                   # Product Requirements Document
├── Roadmap.md               # Project roadmap
├── TechStack.md             # Technology decisions
└── docker-compose.yml       # Local development setup
```

---

## Design Decisions

- **No user accounts** — intentionally sacrificed persistence to polish the learning engine within the 4-day sprint
- **Supabase over SQLite** — cloud PostgreSQL gives instant REST APIs and zero server management
- **LingoCard shared type** — single data contract keeps frontend and backend in sync
- **Visual-First pedagogy** — based on research showing direct concept-to-sound associations build fluency faster than translation-based methods

---

## Team

| Role | Name | Responsibilities |
|------|------|-----------------|
| **Frontend** | Michael (newbloomwon) | React UI, lesson flow, animations, audio |
| **Backend** | Manuel Roman (OasisView) | Express API, Supabase database, CI/CD, testing |

**Project Link:** [github.com/OasisView/BabbleClone](https://github.com/OasisView/BabbleClone)

---

*Built with React, Express, Supabase, and Playwright*
