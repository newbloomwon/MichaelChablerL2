export type LingoCard = {
  id: string;
  type: 'immersive' | 'drill' | 'concept';
  visual_url: string;      // Cloudinary or public URL
  audio_url: string;       // Cloudinary or public URL
  target_text: string;     // Revealed after 2s
  english_bridge?: string; // Revealed on 'Peek' (Drill only)
  grammar_note?: string;   // For ConceptCard
}
