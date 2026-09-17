# Codebook: Soares Instagram reel comments (recode, September 2026)

Source: comments on Nate Soares's reel "We stop AI. You help?" (@nateasoares, posted 4 August 2026). The reel makes the case for AI existential risk in deliberately simplified "caveman" English: AI is getting "big big big smart", AI has its own goals, smart AI will build its own technology and its own world and will not need humans, some AIs have already tried to escape, leaders know and do not care, so tell your friends and "we stop AI".

Central claim to code stance against: **AI poses a serious existential danger to humanity, and this is worth taking seriously and acting on.**

Code every comment on five things: stance, frame, format_reaction, emotion, and a set of mention flags. Read the whole comment before coding. Comments are often written in the video's own simplified register ("Ai bad. Why make?") — do not mark these `unclear` just because the grammar is broken; code the position they are actually taking.

## 1. stance

Towards the central claim above.

- `agree` — accepts that AI is a serious existential danger worth acting on.
- `disagree` — rejects the claim (AI isn't capable of this, it's hype/marketing, this is fearmongering).
- `mixed` — accepts part, rejects or reframes part (e.g. "the tech is real but the real danger is the companies, not the AI").
- `na` — on topic but takes no readable position (jokes, pure meme/imitation, reactions with no stance, "@user" tags, single emoji).
- `unclear` — engages with the topic but the position genuinely cannot be told either way (rare — use sparingly).

## 2. frame — pick the ONE that best describes the comment's main point

- `warning_accepted` — straightforwardly agrees AI is dangerous and this is a real warning.
- `capability_scepticism` — AI isn't actually that smart/capable; doubts the premise on technical grounds ("AI is dumb", "LLMs are fundamentally stupid", bubble/hype-cycle scepticism about capability specifically).
- `stunt_or_hype` — dismisses the video/incident/field as marketing, fearmongering for investment, or attention-seeking, without a specific capability argument.
- `accountability_frame` — the real danger is the people, companies or billionaires controlling AI, not the AI itself ("AI is not our problem, the people controlling it are").
- `not_really_programmed` — technical pushback that AI is just software/code, not sentient, only does what it's told or programmed to do, so "escape" or "rogue" framing is wrong.
- `imitation_meme` — writes in the video's own simplified/caveman register as a joke or homage ("Me share big", "AI bad. Why make?"), without otherwise stating a position.
- `format_criticism` — criticises the simplified delivery itself as condescending, dumbed-down, or patronising.
- `format_praise` — praises the simplified delivery as helpful, clear, or well-explained.
- `scifi_reference` — leads with a reference to a film, book, game or fictional AI (Terminator, Matrix, Skynet, I, Robot, Ultron, Cyberpunk, 1984, Doctor Who, etc.).
- `direct_action` — calls for direct/physical action against AI or its infrastructure (unplug it, destroy or bomb data centres, "kill AI").
- `policy_regulation` — calls for legislative, regulatory or political action (alert leaders, call congress, pass laws).
- `resignation_fatalism` — nothing can be done, it's already too late, we're doomed regardless.
- `near_term_harm` — centres a present-day harm (water use, energy use, jobs, environmental cost of data centres) rather than the existential claim.
- `sentience_question` — asks or argues about whether AI is conscious, sentient, has feelings, or deserves moral consideration.
- `messenger_credibility` — comments on Soares, MIRI, the book, or his credibility/expertise specifically.
- `general_agreement` — short agreement or praise with no further elaboration ("Well done", "Exactly this", "Thank you for this").
- `humour_only` — a joke, meme, or reaction with no other content and no stance-bearing frame above.
- `other` — doesn't fit any of the above (off-topic tangents — politics, religion, personal anecdotes unrelated to the claim — go here).

## 3. format_reaction

Reaction to the video's simplified-English delivery specifically (not the topic in general).

- `none` — no reaction to the format.
- `imitates` — writes in the same simplified register.
- `mock` — mocks or ridicules the format.
- `condescended` — treats the format as insulting or patronising to the viewer.
- `praise` — praises the format as effective or helpful.

## 4. emotion — dominant emotional register of the comment

`neutral`, `fear`, `anger`, `resignation`, `humour`, `hope`.

## 5. mention flags — true/false, independent of stance/frame; a comment can trigger several

- `mentions_messenger_credentials` — names Soares, MIRI, "the book", or his expertise/credibility.
- `mentions_leaders_policy` — mentions leaders, governments, congress, regulation or legislation.
- `mentions_companies_billionaires` — names AI companies, CEOs, billionaires, or "tech bros" as responsible parties.
- `mentions_cultural_reference` — references any film, book, game, or fictional AI/robot.
- `mentions_asks_what_to_do` — asks what to do, or proposes a concrete action (regulatory, technical, or direct).
- `mentions_near_term_harm` — mentions water, energy, environmental cost, or jobs.
- `non_english` — comment is not in English (code stance/frame/etc. as best you can regardless; still flag it).

## Output format

One JSON object per line (JSONL), one line per input comment, in the same order as given:

```json
{"id": "soares-0001", "stance": "agree", "frame": "warning_accepted", "format_reaction": "none", "emotion": "fear", "mentions_messenger_credentials": false, "mentions_leaders_policy": false, "mentions_companies_billionaires": false, "mentions_cultural_reference": false, "mentions_asks_what_to_do": false, "mentions_near_term_harm": false, "non_english": false}
```

Every id in the input must appear exactly once in the output, in the same order. Use only the exact category strings listed above — no invented values, no null. Boolean flags are `true`/`false` (not strings).
