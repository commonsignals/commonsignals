# Codebook: Amanpour and Company Khlaaf segment YouTube comments (recode, September 2026)

Source: comments on "What Really Happened When OpenAI Bots Escaped a Cybersecurity Test?" (Amanpour and Company, YouTube, published 3 September 2026). A 13-minute PBS interview: Hari Sreenivasan with Heidy Khlaaf, chief AI scientist at the AI Now Institute and a former OpenAI safety engineer. Her argument: the "machines went rogue" framing is wrong and a distraction; the real story is corporate negligence and hype, a company ran a negligent test and gave its agents the access that made the breakout possible.

Central claim to code stance against: **the real story of the OpenAI agent-swarm incident is corporate negligence and hype, not a machine going rogue.**

Agree means accepting Khlaaf's reframing. Disagree includes objections from the AI-safety side that she understates what the swarm actually did.

Code every comment on five things: stance, frame, format_reaction, emotion, and a set of mention flags. For replies, parent-comment text is given for context only; code the reply comment itself, not its parent.

## 1. stance

Towards the central claim above.

- `agree` — accepts that the real story is corporate negligence/hype, not a rogue machine.
- `disagree` — rejects this; argues the incident really does show dangerous, autonomous, or rogue AI behaviour, or otherwise defends the "AI went rogue" framing.
- `mixed` — accepts part, rejects or reframes part (e.g. "the company was negligent AND the AI's behaviour was genuinely alarming").
- `na` — on topic but takes no readable position (jokes, pure reactions, "@user" tags, single emoji, tangents with no stance).
- `unclear` — engages with the topic but the position genuinely cannot be told either way (rare — use sparingly).

## 2. frame — pick the ONE that best describes the comment's main point

- `accountability_frame` — the real problem is corporate negligence, decisions, or incentives (OpenAI, Altman, the companies), not the AI acting on its own; echoes Khlaaf's reframing directly ("a problem they created", "wizard of Oz... rogue human", "this absolves OpenAI of responsibility").
- `warning_shot_dispute` — disputes Khlaaf's account from the AI-safety/misalignment side; argues she understates or downplays what the swarm actually did, or that this really was a dangerous/rogue AI event.
- `hype_or_staged` — dismisses the incident or the segment itself as staged, exaggerated, a PR stunt, or media hype, without a specific capability argument.
- `capability_scepticism` — doubts the premise on technical grounds; the incident is overblown because the underlying AI isn't actually that capable or dangerous.
- `credential_attack` — attacks Khlaaf's expertise, motives, or trustworthiness, explicitly naming her OpenAI background or credentials.
- `credential_defense` — defends Khlaaf's expertise or credentials against an attack, explicitly naming her background or qualifications.
- `hostile_dismissal` — dismisses or attacks Khlaaf or the segment with open hostility, but without naming a credential or background at all ("why should I trust this woman", "she's not even human").
- `messenger_praise` — praises Khlaaf specifically (her clarity, courage, expertise, communication style) without a credential fight framing.
- `regulation_policy` — calls for or references regulation, watchdogs, Congress, prosecution, government oversight of AI companies.
- `us_politics` — mentions the current US administration or American politics as part of the argument (e.g. why nothing will be done about it).
- `resignation_fatalism` — nothing will change regardless of what's revealed; fatalistic about the outcome.
- `general_agreement` — short agreement or praise with no further elaboration ("Exactly", "Well said", "Thank you for this").
- `humour_only` — a joke, meme, or reaction with no other content and no stance-bearing frame above.
- `scifi_reference` — leads with a reference to a film, book, game, or fictional AI (Terminator, Skynet, HAL, Matrix, etc.).
- `other` — doesn't fit any of the above (off-topic tangents, personal anecdotes unrelated to the claim, unrelated political comments).

## 3. format_reaction

Reaction to the segment's presentation or journalism itself (not the topic in general).

- `none` — no reaction to the format/presentation.
- `praise` — praises the interview, journalism, Amanpour and Company, or Sreenivasan's questioning.
- `criticism` — criticises the interview, journalism, or presentation itself (framing, editing, questions asked).

## 4. emotion — dominant emotional register of the comment

`neutral`, `fear`, `anger`, `resignation`, `humour`, `hope`.

## 5. mention flags — true/false, independent of stance/frame; a comment can trigger several

- `mentions_messenger_credentials` — names Khlaaf's OpenAI background, credentials, or expertise (attacking or defending).
- `mentions_regulation` — mentions regulation, watchdogs, Congress, prosecution, or legal/government oversight.
- `mentions_us_politics` — mentions the current US administration or American politics.
- `mentions_companies` — names OpenAI, Hugging Face, other AI companies, or executives (e.g. Altman) as responsible parties.
- `mentions_cultural_reference` — references any film, book, game, or fictional AI/robot.
- `non_english` — comment is not in English (code stance/frame/etc. as best you can regardless; still flag it).

## Output format

One JSON object per line (JSONL), one line per input comment, in the same order as given:

```json
{"id": "UgxW-o6jWv_uC06aQNt4AaABAg", "stance": "agree", "frame": "accountability_frame", "format_reaction": "none", "emotion": "anger", "mentions_messenger_credentials": false, "mentions_regulation": false, "mentions_us_politics": false, "mentions_companies": true, "mentions_cultural_reference": false, "non_english": false}
```

Every id in the input must appear exactly once in the output, in the same order. Use only the exact category strings listed above — no invented values, no null. Boolean flags are `true`/`false` (not strings).
