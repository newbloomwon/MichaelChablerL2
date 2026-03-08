require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { supabase } = require('./lib/supabase');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// GET /api/units — list all units
app.get('/api/units', async (req, res) => {
  const { data: units, error } = await supabase
    .from('units')
    .select('id, title, description, language, cards(count)')
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Error fetching units:', error);
    return res.status(500).json({ error: 'Failed to fetch units' });
  }

  res.json({
    units: (units || []).map((u) => ({
      id: u.id,
      title: u.title,
      description: u.description,
      language: u.language,
      card_count: u.cards?.[0]?.count ?? 0,
    })),
  });
});

// GET /api/units/:id — unit detail with ordered cards
app.get('/api/units/:id', async (req, res) => {
  const { id } = req.params;

  const { data: unit, error } = await supabase
    .from('units')
    .select(`
      id, title, description, language,
      cards (
        id, position, type, visual_url, audio_url,
        target_text, english_bridge, grammar_note, sentence
      )
    `)
    .eq('id', id)
    .order('position', { referencedTable: 'cards', ascending: true })
    .single();

  if (error || !unit) {
    return res.status(404).json({ error: 'Unit not found' });
  }

  const cards = (unit.cards || []).map((c) => ({
    id: c.id,
    type: c.type,
    visual_url: c.visual_url,
    audio_url: c.audio_url,
    target_text: c.target_text,
    english_bridge: c.english_bridge || undefined,
    grammar_note: c.grammar_note || undefined,
    sentence: c.sentence || undefined,
  }));

  res.json({
    unit: {
      id: unit.id,
      title: unit.title,
      description: unit.description,
      language: unit.language,
      card_count: cards.length,
    },
    cards,
  });
});

app.listen(PORT, () => {
  console.log(`LingoVision backend running on http://localhost:${PORT}`);
});
