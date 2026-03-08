# ExampleImages: Spanish Language Learning - Common Objects

This file contains curated image examples paired with Spanish vocabulary for the immersive language learning "Day Two" lesson module. Each entry includes:
- **English**: Concept name
- **Spanish (target)**: Word to learn (shown after 2-second delay)
- **Image URL**: High-quality image source (Unsplash/Pexels)
- **Audio phonetic**: Approximate pronunciation guide

---

## Lesson 1: Everyday Objects

### Card 1: Apple
- **English**: Apple
- **Spanish**: Manzana
- **Image**: https://images.unsplash.com/photo-1560806887-1295db8spf93?w=800&q=80
- **Audio**: Pronunciation: "mahn-SAH-nah"
- **Type**: Immersive (Image + Audio → Text reveal at 2s)

### Card 2: Cat
- **English**: Cat
- **Spanish**: Gato
- **Image**: https://images.unsplash.com/photo-1574158622682-e40e69881006?w=800&q=80
- **Audio**: Pronunciation: "GAH-toh"
- **Type**: Immersive

### Card 3: Book
- **English**: Book
- **Spanish**: Libro
- **Image**: https://images.unsplash.com/photo-1507842286343-583f20270319?w=800&q=80
- **Audio**: Pronunciation: "LEE-broh"
- **Type**: Immersive

### Card 4: House
- **English**: House
- **Spanish**: Casa
- **Image**: https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80
- **Audio**: Pronunciation: "KAH-sah"
- **Type**: Immersive

### Card 5: Water
- **English**: Water
- **Spanish**: Agua
- **Image**: https://images.unsplash.com/photo-1509326776104-88b09db1d539?w=800&q=80
- **Audio**: Pronunciation: "AH-gwah"
- **Type**: Immersive

### Card 6: Flower
- **English**: Flower
- **Spanish**: Flor
- **Image**: https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&q=80
- **Audio**: Pronunciation: "FLOHR"
- **Type**: Immersive

### Card 7: Sun
- **English**: Sun
- **Spanish**: Sol
- **Image**: https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800&q=80
- **Audio**: Pronunciation: "SOHL"
- **Type**: Immersive

### Card 8: Tree
- **English**: Tree
- **Spanish**: Árbol
- **Image**: https://images.unsplash.com/photo-1511629179486-dbb1c02cbbc2?w=800&q=80
- **Audio**: Pronunciation: "AHR-bohl"
- **Type**: Immersive

### Card 9: Dog
- **English**: Dog
- **Spanish**: Perro
- **Image**: https://images.unsplash.com/photo-1633722715463-d30628cb6502?w=800&q=80
- **Audio**: Pronunciation: "PEH-rroh"
- **Type**: Immersive

### Card 10: Bread
- **English**: Bread
- **Spanish**: Pan
- **Image**: https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&q=80
- **Audio**: Pronunciation: "PAHN"
- **Type**: Immersive

---

## Metadata

- **Language Pair**: English → Spanish
- **Proficiency Level**: Beginner (A1)
- **Card Count**: 10 immersive cards
- **Lesson Focus**: Visual-First Deciphering (Image + Audio → 2s delay → Target Text)
- **No Translations**: Learners must decode meaning from visual and audio context alone
- **Image Sources**: Unsplash, Pexels (public domain/free commercial use)
- **Audio**: Phonetic pronunciation guide provided; TTS integration recommended for future versions

---

## Implementation Notes

1. **Sequential Reveal Logic**:
   - T=0ms: Image appears, audio plays automatically
   - T=2000ms: Target Spanish text fades in
   - No English translation shown (forces direct association)

2. **Audio Handling**:
   - Use HTML5 `<audio>` with `autoplay` (unlocked after user interaction on splash screen)
   - Alternative: Implement Howler.js for cross-browser audio timing

3. **Image Optimization**:
   - All Unsplash URLs include `w=800&q=80` parameters for mobile optimization
   - Consider caching images locally for offline support (Phase 2)

4. **Accessibility**:
   - Alt text on all images describes the object
   - Phonetic guide provided for text-to-speech fallback
   - Captions/subtitles can be added as toggle for learners with hearing difficulties

5. **Future Extensions**:
   - Add stress/accent marks (e.g., "Á" in "Árbol")
   - Include gender markers (el/la) for nouns
   - Add grammar notes in concept cards
   - Expand to 50+ card lessons as lesson progresses
