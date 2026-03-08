# **PRD: Project "LingoVision" (Babbel-style MVP)**

**Status: Sprint Ready | Timeline: Sunday – Wednesday | Team: Michael (FE), Manuel (BE)**

---

## **1\. Problem Statement**

**The "Translation Trap": Most language apps (like early-stage Babbel or Duolingo) rely heavily on immediate native-language translations. This creates a cognitive "crutch" where the user's brain waits for the English word rather than processing the target language. This slows down natural fluency and prevents users from "thinking" in their new language.**

## **2\. Objective**

**To build a functional language learning interface that uses Visual-First Deciphering. This allows users to "decode" the target language by hearing it and seeing a picture before being confirmed by text, forcing the brain to create direct neural links between concepts and sounds without the intermediate step of translation.**

## **3\. Why This Feature? (Prioritization Logic)**

**We chose the Visual-First Deciphering Engine over other improvements (like Social Features or Voice Rec) based on a High-Impact / High-Feasibility framework:**

* **High Impact: This is our "Unique Selling Point" (USP). It directly addresses the "Translation Trap" and provides the core value proposition of the app.**  
* **High Feasibility: By focusing on a Linear Reveal Logic rather than complex branching or AI-driven speech, we can ensure a bug-free deployment by the Wednesday deadline.**  
* **The Trade-off: We are intentionally sacrificing User Persistence (Accounts) to ensure the Learning Engine is polished and pedagogically sound.**

---

## **4\. The "Introductory Module" Logic**

**Every unit will begin with a Decipher Phase.**

1. **Step 1: User sees a high-quality image and hears the target language audio. (No text visible).**  
2. **Step 2: A 2-second delay occurs (the "thinking gap").**  
3. **Step 3: The Target Language Text appears (fade-in).**  
4. **Step 4 (Later Drills only): The English translation is provided as a secondary "bridge."**

## **5\. "Must-Haves" (For Wednesday Completion)**

### **A. Core Lesson Engine**

* **Audio Trigger: A "Start Unit" button (to bypass browser autoplay blocks).**  
* **Sequential Reveal Logic: Image/Audio $\\rightarrow$ 2s Timer $\\rightarrow$ Target Text Reveal.**  
* **Linear Navigation: "Next" and "Back" buttons for card progression.**  
* **Progress Bar: A simple top-mounted bar showing lesson completion percentage.**

### **B. Card Types**

* **Introductory (Decipher) Card: Image \+ Audio $\\rightarrow$ Target Text only.**  
* **Drill (Review) Card: Image \+ Target Text \+ English Translation (visible or toggleable).**  
* **Linguistic Concept Card: A text-centric card for grammar tips.**

### **C. Technical Infrastructure**

* **Static JSON API: Manuel provides endpoints for /units and /units/:id.**  
* **Cloud Hosting: Images/Audio hosted on Cloudinary or S3.**  
* **Deployment: Vercel (Frontend) and Render/Railway (Backend).**

---

## **6\. "Must-Not-Do" (Strictly Out of Scope)**

**❌ User Accounts: No Sign-up, Login, or Profile pictures.**

**❌ Persistence: No "saving progress" to a database yet; use local state only.**

**❌ Speech Recognition: No "record your voice" features.**

**❌ Content Management UI: Manuel should manage content in the DB/JSON directly.**

**❌ Complex Animations: Stick to simple CSS opacity transitions.**

---

## **7\. Success Criteria**

1. **A user can visit the site and click "Start."**  
2. **The user completes a 10-card unit following the Image $\\rightarrow$ Audio $\\rightarrow$ Text sequence.**  
3. **The transition from the "Introductory" card (no English) to "Drill" cards (with English) is clear.**  
4. **The app functions smoothly on both Desktop and Mobile browsers.**

