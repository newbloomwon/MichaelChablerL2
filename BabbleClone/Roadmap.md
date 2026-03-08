To build the **"Cognitive Deciphering"** engine within your aggressive 3.5-day timeline, your tech stack must prioritize **asynchronous timing**, **media delivery speed**, and **unified data types**.

Based on your updated roadmap, here is the optimized "LingoVision" tech stack.

---

## **🛠️ Unified "LingoVision" Stack (2026)**

### **Frontend (Michael)**

**Focus:** The "Thinking Gap" Logic & Visual-First UX

* **Framework:** **Next.js 15+ (App Router)**  
  * *Why:* Next.js 15’s "Client Island" architecture is perfect for isolating the high-interactivity ImmersiveCard. It allows for instant loading of the image while the audio and text "hydration" happens in the background.  
* **Styling & Animation:** **Tailwind CSS \+ Framer Motion**  
  * *Why:* Use Tailwind for layout speed. Use **Framer Motion** for the "Decoded" reveal. Its animate={{ opacity: 1 }} with a delay: 2.0 is the cleanest way to implement the "Thinking Gap" without messy setTimeout chains.  
* **State Management:** **Zustand**  
  * *Why:* You need a global lessonStore to track currentStep (Decipher vs. Drill) and isDecoded. Zustand is 10x faster to set up than Redux for a 3-day sprint.  
* **Audio Engine:** **Howler.js**  
  * *Why:* Standard HTML5 audio can be finicky with timing. Howler provides a reliable .play() method that works across mobile browsers once "unlocked" by your Splash Screen.

### **Backend (Manuel)**

**Focus:** Asset Delivery & "Agentic-Ready" Data

* **Platform:** **Supabase (PostgreSQL)**  
  * *Why:* **Speed.** You get a database, instant REST APIs, and Auth (for Phase 5\) with zero boilerplate. Manuel can define the Units table in the UI and Michael can fetch from it immediately.  
* **Media Hosting:** **Cloudinary (AI-Optimized)**  
  * *Why:* Cloudinary’s "Auto-format" (f\_auto) and "Auto-quality" (q\_auto) are essential. It ensures the high-res images needed for "Visual-First" decoding load instantly, even on weak mobile connections.  
* **Server Logic:** **Next.js Route Handlers (Edge Runtime)**  
  * *Why:* Since you're already using Next.js, Manuel can write "Backend" logic directly in /app/api. Using the **Edge Runtime** ensures \<10ms latency for fetching the next card.

---

## **🏗️ The "Association" Data Model**

To ensure Michael and Manuel stay in sync, use this shared JSON structure for your cards:

TypeScript

```

type LingoCard = {
  id: string;
  type: 'immersive' | 'drill' | 'concept';
  visual_url: string;      // Cloudinary URL
  audio_url: string;       // Cloudinary URL
  target_text: string;     // Revealed after 2s
  english_bridge?: string; // Revealed on 'Peek' (Drill only)
  grammar_note?: string;   // For ConceptCard
}

```

---

## **📊 Tech Comparison Table**

| Component | Choice (Speed) | Alternative (Control) | Why for LingoVision? |
| :---- | :---- | :---- | :---- |
| **Frontend** | **Next.js 15** | Vite \+ React | Best-in-class media optimization. |
| **Styling** | **Tailwind** | CSS Modules | Zero-config "Thinking Gap" animations. |
| **Database** | **Supabase** | MongoDB Atlas | Instant API generation (Manuel saves 4 hours). |
| **Media** | **Cloudinary** | AWS S3 | Automatic image resizing for mobile "decoding." |
| **Deployment** | **Vercel** | AWS | Git-push to deploy ensures Wednesday launch. |

---

### **💡 Pro-Tip for Michael: The "Autoplay" Unlock**

Browsers will block your 2-second audio reveal unless the user interacts first.

1. Create a **"Start Unit"** button on the splash screen.  
2. On click, initialize a "Silent" Howler instance: new Howl({ src: \['silent.mp3'\] }).play();.  
3. This **"unlocks"** the audio context, allowing all subsequent cards in that unit to play audio automatically and perfectly timed with your image reveal.

**Would you like me to generate the Supabase Schema for Manuel so he can set up the database in 5 minutes?**

