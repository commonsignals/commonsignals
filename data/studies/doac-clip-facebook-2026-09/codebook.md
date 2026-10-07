# Codebook: DOAC AI debate comments (October 2026)

Version 2 (6 October 2026). Version 1 is kept as `codebook_v1.md`. Version 2 defines `unclear` against `na` and against taking a side, and adds the frame tie-breaks for `debater_verdict` and `other`. Allowed values are unchanged.

## Context

The artefact is the Diary of a CEO episode "AI Experts Debate: The AI Labs Are Lying To Everyone, Is There A 99% Chance Of Human Extinction?" (17 September 2026), with Nate Soares and Roman Yampolskiy arguing that advanced AI poses an extinction-level risk, Andrew McAfee arguing the risk is near zero, and Ed Zitron arguing that present-day harms and industry hype matter more. Comments come from the full episode on YouTube and from a 104-second clip of Soares posted on YouTube Shorts, TikTok, Instagram and Facebook. In the clip Soares says AI's benefits and present harms can both be real, but neither answers what happens if AI becomes far more capable than humans.

The audience is the general public who follow a mainstream business and self-improvement podcast, not an AI-specialist audience.

## Central claim (for stance)

Advanced AI could become impossible for humans to control and poses a serious risk, up to human extinction, that justifies slowing or stopping development.

## Coder instructions

- Code what the comment says, not who wrote it.
- Replies come with their parent's text in `parent_text`. Use it to understand what the reply is responding to, but code the reply itself.
- When a comment fits two frames, pick the one it leads with, except where the frame tie-breaks below say otherwise.
- Siding with a debater counts as stance. Praising Soares or Yampolskiy, or attacking the sceptic, is `agree`; praising the sceptic or attacking Soares or Yampolskiy is `disagree`. Commenters refer to Andrew McAfee as "the bald guy", "let me finish guy" or "the 0% guy". Ed Zitron is on neither side: praise or criticism of him alone is `na` unless the comment also takes a position on the claim.
- Comments purely about the format, adverts, the host or production are `na` with frame `format_only`.
- Use only the allowed values below. Output one JSON object per line, one per input id, and nothing else.

## Dimensions

**stance**: `agree`, `disagree`, `mixed`, `unclear`, `na` (off topic, tag-only, emoji-only, or purely about the format or speaker without taking a side).

Telling `unclear` from `na` and from a side:

- `na`: the comment does not engage with AI or AI risk at all. Examples: tags, emoji, greetings, "great episode", comments about the host, adverts, production or guest requests, praise or criticism of Ed Zitron alone, and jokes or chat with no bearing on AI.
- `unclear`: the comment is about AI, AI risk or the debate's argument, but you cannot tell whether it accepts or rejects the central claim. Examples: neutral questions ("how would it get power?"), observations about AI with no evaluation, sarcasm whose target you cannot identify.
- `agree` or `disagree`: the position on the central claim, or the side taken under the siding rule above, can be read from the comment, using `parent_text` only to resolve what the reply refers to. Tone, alarm or a joke alone is not a position: if you would have to guess, use `unclear`.
- `mixed`: the comment explicitly holds both positions (for example, the risk is real but the extinction claims are overblown).

**frame** (one per comment):

| Key | Definition | Example from the thread |
| --- | --- | --- |
| `general_agreement` | Agrees with the risk case without giving a further reason | "This really is the whole argument in one sentence." |
| `debater_verdict` | Judges the panellists (who won, who was rude, who talked too much) more than the argument | "Pretty sure AI is already smarter than the bald guy" |
| `fatalism` | Doom, too late, resignation, grief for the future | "We're all doomed...there's no other way of putting it." |
| `scifi` | Reads the risk through a film, TV or book story | "Strong 'Don't Look Up' vibes with this interview." |
| `blame_people` | The danger is the humans who control or misuse AI (greed, power, bad actors), not AI itself | "the main risk is people with such enormous power going rogue" |
| `human_mirror` | AI is dangerous because it is trained on and copies human nature | "you design an artificial mind based on humans and it acts like humans" |
| `capability_scepticism` | AI is just a tool or LLM, it is hype, the fear is scaremongering | "AI is so dumb. What are you talking about" |
| `unplug` | We can switch it off, cut power or destroy data centres, or rebuttals that we cannot | "Can't we just unplug it ?" |
| `takeover_scenarios` | Speculation about how AI would harm or outwit us: hiding, replicating, sabotage, competing for resources | "We won't be seen as cattle more like weeds" |
| `policy_leaders` | Regulation, slowing down, prosecuting executives, political leaders, international race | "Roman should speak to congress" |
| `present_harms` | Harms happening now: jobs, education, dependence, misuse today | "we stopped paying attention to what's happening now" |
| `benefits` | AI's upside, or that the risk is worth taking | "I would love to use AI to discover a cure" |
| `religion_spiritual` | Religious or spiritual reading | "No one here wants to consider Revelation ch 13?" |
| `conspiracy_other_target` | Conspiracy theories aimed at groups or institutions | "Scare mongering, just like covid, fals flag incoming" |
| `format_only` | About the podcast itself: format, adverts, guests requested | "Thumbs down for all these advertisement breaks." |
| `other` | Fits none of the above | |

Frame tie-breaks:

- **`debater_verdict` against an argument frame.** Use `debater_verdict` only when judging the panellists is the substance of the comment: who won, who was rude, who interrupted, who talked too much, insults or praise with no argument about AI. If the comment also makes an argument that fits another frame (for example, that we could unplug AI, that AI is hype, that it is too late, that greedy companies are the danger), code that frame instead, however the comment opens. Stance still follows the siding rule, and the `m_risk_debater` and `m_sceptic_debater` flags record that a debater was named.
- **`other` is a last resort.** Before coding `other`, check that no listed frame fits:
  - A comment that agrees with the risk case and adds nothing else is `general_agreement`, however short.
  - A comment about the podcast, host, adverts, production or guest requests is `format_only`.
  - A comment that dismisses the risk without a reason ("nonsense", "fearmongering") is `capability_scepticism`.
  - Use `other` only for comments that fit none of these or any other frame.

**format_reaction**: `praise`, `mock`, `condescended`, `imitates`, `none`. Refers to the delivery of the artefact (the debate or the clip), not to individual debaters' manners, which go under `debater_verdict`.

**emotion**: `fear`, `resignation`, `anger`, `humour`, `hope`, `neutral`.

**Mention flags** (0 or 1):

- `m_messenger_credentials`: mentions a speaker's expertise, credentials, book or track record.
- `m_leaders_policy`: mentions governments, politicians, regulation or law.
- `m_companies_billionaires`: mentions AI companies, their executives or billionaires.
- `m_cultural_reference`: mentions a film, TV show, book or meme.
- `m_asks_what_to_do`: asks a genuine question about what people or society can do ("what can we do?", "how do we stop it?"). Commands such as "pull the plug now" are 0.
- `non_english`: written mainly in a language other than English.
- `m_risk_debater`: names or refers to Soares or Yampolskiy.
- `m_sceptic_debater`: names or refers to McAfee.
- `m_china_other_nations`: mentions China or competition between countries.
- `m_incident`: refers to the OpenAI agent-swarm or Hugging Face incident discussed in the episode.

## Output format

One line per comment, exactly:

{"id": "...", "stance": "agree", "frame": "fatalism", "format_reaction": "none", "emotion": "resignation", "m_messenger_credentials": 0, "m_leaders_policy": 0, "m_companies_billionaires": 0, "m_cultural_reference": 0, "m_asks_what_to_do": 0, "non_english": 0, "m_risk_debater": 0, "m_sceptic_debater": 0, "m_china_other_nations": 0, "m_incident": 0}

## Rows not sent to coders

Rows flagged `cta_keyword` (Instagram "Debate"/"DM" replies to the caption's DM offer), `emoji_only`, `no_text` and `featured_messenger` (Soares's own comment) are assigned stance `na`, frame `other`, emotion `neutral` and all flags 0 at merge, and are excluded from frame shares.
