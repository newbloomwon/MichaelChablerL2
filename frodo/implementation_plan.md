# Frodo: Phase I Integrated Master Plan (The "Ring-Bearer" Edition)

## Goal Description
Build "Frodo", a "Strategic Invisibility" platform designed to identify and destroy "Shadow Profiles" created by data brokers. The app guides users through a 5-step emotional journey from vulnerability to sanctuary, using a High-Fantasy / Digital-Ethereal aesthetic.

## User Review Required
> [!IMPORTANT]
> **Mock Backend Logic**: Confirm the specific string triggers for the `/api/scan` endpoint (e.g. `email.includes('risk')`).
> **Aesthetic Direction**: Confirm "Dark Mithril" theme specifics (colors, fonts).

## Proposed Changes

### Project Setup
#### [NEW] [frodo-app]
- Initialize Next.js 14+ (App Router) project found at `c:\Users\micha\.gemini\antigravity\scratch\frodo\frodo-app`.
- Configure Tailwind CSS.
- Install dependencies: `framer-motion`, `lucide-react`.

### Components
#### [NEW] [TheShire.tsx]
- Minimalist landing page with email entry.
- Triggers FSM transition to SCANNING.

#### [NEW] [ThePalantir.tsx]
- "Deep Scan" terminal visualizer.
- Simulates API call delay.

#### [NEW] [AdversaryHUD.tsx]
- Displays "Nazgûl" SVG/Canvas visual.
- Renders `AdversaryCards` (Identity, Physical, Digital).
- Uses `useTethers` hook for connecting lines.

#### [NEW] [DestructionOverlay.tsx]
- Handles "Cast into Fire" interaction.
- Renders particle explosion effect.

#### [NEW] [TheHavens.tsx]
- "Safe" dashboard state.
- Displays comprehensive deleted data log.

### Logic
#### [NEW] [useFrodoMachine.ts]
- Custom hook implementing FSM: `IDLE` -> `SCANNING` -> `ADVERSARY` -> `SAFE`.

#### [NEW] [api/scan/route.ts]
- Mock API route handling POST requests.
- Returns threat payload based on email triggers.

## Verification Plan
### Manual Verification
- **Flow Test**: Walk through the "Shire" -> "Palantir" -> "Wraith" -> "Fire" -> "Havens" sequence.
- **Persistence**: Refresh page at "Havens" state to verify user remains "Safe".
- **Visuals**: Check "Dark Mithril" theme and Nazgûl rendering.
