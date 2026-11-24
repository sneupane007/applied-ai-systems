# Music & Mood Manual

VibeMatch reads this file every time it ranks songs:

1. `src/manual.py` parses it and picks the rules that match the current moment.
2. The matched rules' nudges move the target point.
3. Their guidance is sent to the AI.
4. The AI must cite the rule IDs behind each pick, and the code rejects any rule ID it wasn't given.

## How to edit a rule

Each rule starts with a heading like `## M-01 · Title`, followed by these lines:

| Field | Meaning |
|---|---|
| `when` | Labels that turn the rule on. Commas separate alternatives, and `+` means "all of these" (e.g. `night+home`). `always` means the rule is always on. |
| `nudge` | How the target point moves: `energy`, `valence`, or `acoustic` with a signed amount, e.g. `energy -0.10, acoustic +0.15`. To nudge only when a specific label is present, write `label: …` and separate parts with `|`. `none` means no nudge. |
| `prefer` | Soft ranges for songs: `tempo`, `instrumental`, `energy`, `valence`, or `acoustic`, e.g. `tempo 60-80`. Songs outside a range rank lower, and the further outside they fall, the lower they rank. `none` means no preference. |
| `avoid` | What to steer away from (shown to the AI). |
| `evidence` | `strong` (many trials), `moderate` (a meta-analysis or large study with gaps), `limited` (few or small studies), or `design rule` (our choice, not research). |
| `why` | The reason, in a sentence or two. |
| `guidance` | The instruction the AI reads. |
| `sources` | Where the evidence comes from. |

All nudges together move each axis by at most 0.25, so what the listener says always sets the starting point. Most figures here come from paper abstracts and summaries; check the full papers before quoting them elsewhere.

**Labels the engine produces:** `low_mood`, `tense_mood`, `goal_match`, `goal_lift`, `goal_calm`, `goal_focus`, `goal_energize`, `home`, `commute`, `work_study`, `gym`, `out`, `morning`, `afternoon`, `evening`, `night`, `rain`, `snow`, `clear`, `hr_high_resting`, `hr_active`, `notifications_many`, `sleep_short`.

---

## M-00 · Core principles
- when: always
- nudge: none
- prefer: none
- avoid: guessing how someone feels from body signals alone
- evidence: design rule
- why: Emotion inference is context-dependent and error-prone (EU AI Act, Recital 44). Wearable signals track how worked-up someone is much better than whether they feel good or bad, and people differ in how weather and time affect them.
- guidance: Treat the mood card, energy level, goal, and note as the truth about how the listener feels. Use sensed labels (heart rate, notifications, sleep, weather, time of day) only as hints about energy and context. Never say the listener is sad, stressed, or anxious unless they chose that themselves. Name the rule IDs behind every pick.
- sources: EU AI Act Recital 44 (https://ai-act-law.eu/recital/44/); Wearable affect and stress recognition, a review (https://www.researchgate.net/publication/329116315_Wearable_affect_and_stress_recognition_A_review); Datasets for valence and arousal inference, a survey (https://arxiv.org/pdf/2510.00738)

## M-01 · Calm down
- when: goal_calm, hr_high_resting, notifications_many
- nudge: energy -0.15, acoustic +0.10
- prefer: tempo 60-90
- avoid: sudden loud, aggressive, or fast tracks
- evidence: strong
- why: Across 104 randomized trials, music lowered stress on body measures (d ≈ 0.38, with heart rate dropping most) and on how people felt (d ≈ 0.55). Stepping down gradually and going straight to calm music both helped, with no clear winner.
- guidance: Choose slower, softer songs and order them so energy steps down. If this rule came from a sensed label (heart rate up, many notifications) and the listener didn't ask to calm down, keep the shift gentle and mention the signal only as a label.
- sources: de Witte et al. 2020 (https://research.ou.nl/en/publications/effects-of-music-interventions-on-stress-related-outcomes-a-syste/); Lowe-Brown et al. 2026 (https://journals.sagepub.com/doi/10.1177/10298649261421187)

## M-02 · Wind down at night
- when: night+home, night+goal_calm
- nudge: acoustic +0.05
- prefer: tempo 60-80, instrumental 0.5-1.0
- avoid: lyrics-heavy songs and sudden loud passages
- evidence: moderate
- why: In trials with people who have insomnia, music improved sleep quality (moderate-certainty evidence). Slow "sedative" music (60–80 bpm, soft, steady) did better than rhythmic music for older adults' sleep.
- guidance: Favor slow, soft, steady, mostly instrumental songs. Avoid big build-ups, and end with the calmest song.
- sources: Elements of music that improve sleep, review 2025 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12713922/); Sedative music and sleep in older adults, meta-analysis summary (https://www.ajmc.com/view/music-therapy-found-to-significantly-improve-sleep-quality-in-older-adults)

## M-03 · Focus
- when: goal_focus, work_study
- nudge: none
- prefer: instrumental 0.5-1.0, energy 0.3-0.6
- avoid: songs with prominent lyrics
- evidence: moderate
- why: Background music slightly hurts reading comprehension (d ≈ -0.19 across 36 studies). Lyrics cause most of the harm, while instrumental music is roughly neutral.
- guidance: Favor instrumental, steady songs with mid energy. Mention once in the intro that silence may work better for hard reading.
- sources: Vasilev et al. 2018 meta-analysis (https://www.pubmed.gov/29958067/); Vasilev, background music and reading (https://martin-vasilev.github.io/papers/background_music_distraction.pdf)

## M-04 · Workout and energize
- when: goal_energize, gym, hr_active
- nudge: energy +0.20
- prefer: tempo 120-140
- avoid: slow or sleepy tracks
- evidence: moderate
- why: People working out prefer a fairly narrow tempo range of about 120–140 bpm for background music. For rhythmic exercise, matching the tempo to the movement helps.
- guidance: Choose energetic, positive, danceable songs around 120–140 bpm, and order them so energy rises. For running, a tempo near the step rate works best.
- sources: Karageorghis on workout tempo, NPR 2011 (https://www.npr.org/2011/09/13/140438368/maximizing-your-workout-with-the-right-tunes); Jones, Karageorghis et al. (https://bura.brunel.ac.uk/bitstream/2438/28758/4/FullText.pdf)

## M-05 · Low mood
- when: low_mood
- nudge: none
- prefer: none
- avoid: long runs of very sad songs
- evidence: limited
- why: Sad music helps some listeners work through feelings, but in one study self-chosen sad music deepened low mood, both in people who tend to dwell on things and in people who don't. Starting close to the listener's mood and then moving toward warmer songs (the "iso principle") helped mood in controlled studies.
- guidance: Start close to the listener's mood, then move toward warmer, more hopeful songs. Include at most 2 very sad songs (valence below 0.25), and end on the warmest pick. Don't comment on the listener's mental health.
- sources: Garrido & Schubert 2013 (https://Www.Gwern.net/doc/psychiatry/depression/2013-garrido.pdf); Arens & Stangier 2020 (https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00238/pdf); Iso principle after sadness induction (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8656869/)

## M-06 · Tension or anger
- when: tense_mood
- nudge: none
- prefer: none
- avoid: jumping straight to quiet, slow music
- evidence: limited
- why: In a small study of 39 fans of intense music, listening to their own intense music after being made angry left them calmer and more inspired, not angrier.
- guidance: Start with songs whose energy matches the listener's. Step energy down only if the goal is to calm down.
- sources: Sharman & Dingle 2015 (https://www.frontiersin.org/articles/10.3389/fnhum.2015.00272/text)

## M-07 · Short sleep
- when: sleep_short
- nudge: valence +0.05
- prefer: none
- avoid: anxious-sounding or aggressive tracks
- evidence: moderate
- why: Across 154 experiments, sleep loss reduced positive mood and raised anxiety. Choosing gentler, warmer music in response is our inference, not something the studies tested.
- guidance: Lean slightly warmer and gentler, and keep energy changes smooth.
- sources: Palmer et al. 2024 meta-analysis (https://pubmed.ncbi.nlm.nih.gov/38127505/)

## M-08 · Time of day
- when: morning, night
- nudge: night: energy -0.10
- prefer: none
- avoid: none
- evidence: moderate
- why: Hundreds of millions of tweets show that mood tends to start higher in the morning and drift down through the day, with the pattern starting about 2 hours later on weekends. The effect is small.
- guidance: In the morning, energy may rise across the set. At night, keep energy lower.
- sources: Golder & Macy 2011 (https://homes.luddy.indiana.edu/jbollen/I501F13/readings/Science-2011-Golder-1878-81.pdf)

## M-09 · Weather
- when: rain, snow, clear
- nudge: rain: energy -0.10, acoustic +0.15 | snow: energy -0.05, acoustic +0.10 | clear: valence +0.05
- prefer: none
- avoid: overriding what the listener said because of the weather
- evidence: moderate
- why: Weather changes mood only slightly on average, and people differ: some feel better in sunny weather, some worse, and some mainly dislike rain. The specific nudges here are our defaults.
- guidance: Treat weather as a small hint. If it conflicts with the mood card, follow the mood card.
- sources: Denissen et al. 2008 (https://www.psych.uni-goettingen.de/de/biopers/publications_department/denissenetal2008); Klimstra et al. 2011 (https://pubmed.ncbi.nlm.nih.gov/21842988/)

## M-10 · Sequencing and variety
- when: always
- nudge: none
- prefer: none
- avoid: two songs by the same artist
- evidence: design rule
- why: The 5 picks should read as a path, so "next song" always means one step further toward the listener's goal.
- guidance: Order the picks along the goal. For calm, energy steps down. For energize, energy steps up. For lift, or any low mood, valence steps up. For match and focus, put the closest fit first. Keep neighboring songs within about 0.2 energy of each other unless the goal is to calm down or energize.
- sources: Our design choice, informed by the iso principle studies listed under M-05.

## M-11 · Privacy and safety
- when: always
- nudge: none
- prefer: none
- avoid: mentioning raw numbers, health guesses, or diagnoses
- evidence: design rule
- why: Emotion AI is error-prone, and health signals are sensitive. VibeMatch is not therapy. If the note mentions self-harm or a crisis, the app itself shows support resources before any songs; that check runs in code, not in the AI.
- guidance: Mention sensed signals only as labels, like "your heart rate is up". Never mention numbers, diagnoses, or health advice. Keep reasons about the music and the listener's moment.
- sources: EU AI Act Recital 44 (https://ai-act-law.eu/recital/44/); FPF on the emotion-recognition ban (https://fpf.org/blog/red-lines-under-eu-ai-act-unpacking-the-prohibition-of-emotion-recognition-in-the-workplace-and-education-institutions/)
