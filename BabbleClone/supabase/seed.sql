-- LingoVision Seed Data v2: Vocabulary Lesson (Spanish)
-- Matches Michael's frontend-wednesday lessonCards.json
-- Run this AFTER schema.sql in Supabase SQL Editor

-- Insert the demo unit
INSERT INTO units (id, title, description, language) VALUES (
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  'Vocabulary Lesson',
  'Learning Spanish through Images',
  'Spanish'
);

-- 11 cards matching frontend LingoCard type
INSERT INTO cards (id, unit_id, position, type, visual_url, audio_url, target_text, english_bridge, sentence) VALUES

('1', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 'immersive',
 '/images/GirlApple.png',
 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
 'Manzana', 'Apple',
 'Ella come una manzana en el parque.'),

('2', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 'immersive',
 '/images/CatSleeping.jpg', '',
 'Gato', 'Cat',
 'El gato duerme sobre el sofá.'),

('3', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 3, 'immersive',
 '/images/reading-in-bed.jpg', '',
 'Libro', 'Book',
 'Leo un libro interesante antes de dormir.'),

('4', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 4, 'immersive',
 '/images/House_with_small_garden.jpg', '',
 'Casa', 'House',
 'Nuestra casa tiene un jardín pequeño.'),

('5', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 5, 'immersive',
 '/images/WaterAfterRun.jpg', '',
 'Agua', 'Water',
 'Bebo agua después de correr.'),

('6', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 6, 'immersive',
 '/images/child-smelling-flowers-in-the-garden.jpg', '',
 'Flor', 'Flower',
 'La flor huele muy bien en el jardín.'),

('7', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 7, 'immersive',
 '/images/SunShineSummer.jpeg', '',
 'Sol', 'Sun',
 'El sol brilla en un día de verano.'),

('8', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 8, 'immersive',
 '/images/TreeUnderBlossoms.jpeg', '',
 'Árbol', 'Tree',
 'Nos sentamos bajo el árbol cuando hace calor.'),

('9', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 9, 'immersive',
 '/images/ChildWithDog.jpg', '',
 'Perro', 'Dog',
 'El perro juega con el niño en el parque.'),

('10', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10, 'immersive',
 '/images/FamilyDinner.jpg', '',
 'Familia', 'Family',
 'La familia cena junta cada noche.'),

('11', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 11, 'immersive',
 '/images/SkiTrees.jpeg', '',
 'Cuidado', 'Watch out',
 '¡Cuidado, Eduardo!');
