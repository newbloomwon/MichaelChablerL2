# PRD: Discografy - Real Music for Real People

## 1. Product Vision
"People are hungry for music, not muzak." Discografy is the antithesis of the "lean back" algorithmic streaming experience. We empower human curators and discovery-hungry fans to find the next great artists before they become background noise.

## 2. The Defensible Moat: Taste Leadership & Exclusive Talent

A competitive moat is not just a message; it is a structural barrier. Discografy’s moat is built on:

*   **Identified Taste Leadership**: Unlike Spotify’s anonymous "Editors," our curators are known entities (e.g., genre experts, influencers) with loyal fanbases. The relationship is between the **Curator and Fan**, not the User and Algorithm.
*   **The "Emerging Talent" Pipeline**: By offering artists higher royalties (e.g., 80% vs 70%) in exchange for **temporary exclusivity** (e.g., first 3 months of a release), we create a high-value destination. If you want the "New Sound of Alt-Rock," you *have* to be on Discografy.
*   **Curator Network Effects**: Each curated "crate" becomes a social asset. When a curator shares their crate, they bring their audience to Discografy, lowering our platform-wide CAC and creating a barrier to exit for the fans following those curators.

## 3. Unit Economics: The Discovery Math

To survive on thin margins, we must optimize the **LTV:CAC Ratio**.

### Assumptions:
*   **CAC (Customer Acquisition Cost)**: ~$3.00 (Targeted YouTube Ad via Professor of Rock style channels).
*   **LTV (Lifetime Value)**:
    *   Discovery Fee (Discografy Cut): $0.30 per download.
    *   Frequency: Active discovery users download ~15 songs/year.
    *   Gross Profit per user: $4.50/year.
    *   Expected lifespan: 2 years.
    *   **Total LTV**: $9.00.
*   **LTV:CAC Ratio**: 3:1 (Healthy for a seed-stage product).

### Economic Levers:
*   **Exclusivity Margin**: Exclusive tracks can command a higher discovery fee or a premium "Early Access" subscription.
*   **Virality**: Curator sharing lowers Blended CAC by acquiring users organically.

## 4. Path to Profitability

1.  **Phase 1: Validation (Months 1-6)**: Prove the CAC assumptions. Focus on 2-3 core genres (e.g., Alt-Rock, Indie).
2.  **Phase 2: Scale (Months 6-18)**: Launch the Curator Dashboard. Incentivize curators with a share of the download revenue, turning them into a decentralized sales force.
3.  **Phase 3: Margin Expansion (18+ Months)**: Introduce "Discografy Pro" for artists (data analytics) and fans (ad-free discovery + collector badges).

## 5. Core Features (Current Focus)
*   **Random Discovery Engine**: A high-friction (intentional) discovery UI that rewards active listening.
*   **Curated Crates**: The basic unit of organization, tied to a human curator.
*   **One-Tap Download**: Frictionless acquisition of "Real Music."

## 6. Implementation Status (Alpha)
*   **Current Build**: Prototype v0.2.
*   **Key Features Active**:
    *   **Audio Player**: Functional play/pause, volume control, track seeking. Fixed Bluetooth/Audio context issues.
    *   **Random Discovery**: "Spin to Win" mechanism implemented for Alt-Rock genre (Prototype in `dev-random-tab`).
    *   **Firebase Integration**: Configured and initialized (API keys secured).

## 7. Design System
*   **Theme**: "Tactile In Rainbows" meets "Nature's Palette".
*   **Color Palette**:
    *   **Sky Blue**: Primary accents.
    *   **Forest Green**: Secondary elements, success states.
    *   **Rock Beige**: Backgrounds, panels.
    *   **Red**: Highlights/Alerts.
*   **Typography**: Clean, sans-serif, high readability.

## 8. Technical Stack
*   **Frontend**: Vanilla HTML/CSS/JS.
*   **Desktop Wrapper**: Electron.
*   **Backend/Data**: Firebase (Firestore/Auth/Storage).
*   **Hosting**: GitHub Pages (for web demo), Electron Builder (for desktop distribution).
