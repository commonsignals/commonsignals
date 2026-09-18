# Codebook: X replies to Jacob Coxon's Anthropic resignation thread (September 2026)

Source: replies to [Jacob Coxon](https://x.com/hilbertspaess)'s seven-tweet thread on X, posted 9 September 2026. First line: "I resigned from Anthropic today. I spent the last three years doing pretraining research at both OpenAI and Anthropic. Neither company is acting responsibly. They are racing straight to self-improving superintelligence and gambling with our lives." Six more posts elaborated the argument.

Central claim to code stance against: **neither OpenAI nor Anthropic is acting responsibly with frontier AI, and both are racing toward dangerous self-improving superintelligence.**

This codebook documents the scheme reflected in the delivered coded dataset; no separate coder brief was archived ahead of coding, so it was reconstructed from the data itself and the published article rather than transcribed from an original prompt.

Code every reply on five things: stance, frame, format_reaction, emotion, and a set of mention flags. Quote-tweets, the parent tweet's text and prior replies in the thread are not supplied as context — code the reply as posted.

## 1. stance

Towards the central claim above.

- `agree` — accepts that neither company is acting responsibly and the danger described is real.
- `disagree` — rejects this, on any grounds (capability scepticism, geopolitics, IPO cynicism, or defending the labs).
- `mixed` — accepts part of the danger claim while rejecting or reframing another part (for example, disputing that resigning was the right response).
- `na` — on topic but takes no readable position (jokes, pure reactions, single-line replies with no argument).
- `unclear` — engages with the topic but the position genuinely cannot be told either way (rare — use sparingly).

## 2. frame — pick the ONE that best describes the comment's main point

- `capability_scepticism` — doubts current or near-term AI can do what Coxon describes.
- `china_race` — argues unilateral restraint just hands the advantage to China or another geopolitical rival.
- `format_only` — reacts only to the thread's tone, length or format rather than its content ("Well this was a pleasant read right before bed.").
- `general_agreement` — endorsement without a distinct argument.
- `technical_argument` — makes a substantive technical claim about how the danger would or wouldn't unfold.
- `blame_people` — accepts the danger is real but locates the fault in human greed, elitism or the desire for control rather than the technology itself.
- `how_to_act` — asks or proposes what an ordinary person, or anyone, should actually do in response.
- `scifi` — frames the claim through film, book, game or other fiction.
- `hypocrisy_critique` — argues that quitting is the wrong response if Coxon genuinely believes what he says.
- `messenger_authenticity` — questions or defends whether Coxon's resignation and stated motives are genuine, as opposed to arguing about the danger claim itself.
- `ipo_marketing_cynicism` — reads the whole thread as promotional and timed to Anthropic's pending IPO.
- `fatalism` — accepts the danger but responds with resignation or nihilism rather than a call to act.
- `conspiracy_other_target` — reframes the thread as a paid, staged or PR operation for Anthropic, OpenAI or another party, rather than a sincere resignation.
- `religion_spiritual` — frames the danger, or Coxon's role, in religious or spiritual terms.
- `present_harms` — argues the more pressing danger is nearer-term harm (jobs, economic disruption) rather than existential risk.
- `benefits` — argues AI's benefits outweigh the risk described, or that stopping or slowing development is the real danger.
- `other` — doesn't fit any of the above (off-topic tangents, undifferentiated hostility).

## 3. format_reaction

Reaction to Coxon and the thread as a piece of writing (not the danger argument itself). Note this is a study-specific vocabulary, not the interview-reaction set used for the Amanpour segment — there is no interview here to react to.

- `none` — no distinct reaction to the thread as writing.
- `mock` — mocks or ridicules the thread, Coxon, or the situation.
- `condescended` — responds with a condescending or patronising tone toward Coxon.
- `imitates` — imitates or parodies Coxon's writing style or voice.
- `praise` — praises Coxon, the thread, or the decision to write and post it.

## 4. emotion — dominant emotional register of the comment

`neutral`, `fear`, `anger`, `resignation`, `humour`, `hope`.

## 5. mention flags — true/false, independent of stance/frame; a comment can trigger several

- `mentions_messenger_credentials` — names Coxon's own career history, credentials, or trustworthiness as the messenger (attacking or defending).
- `mentions_leaders_policy` — governments, regulators, politicians, treaties, courts, law.
- `mentions_companies_billionaires` — names companies, investors, billionaires, bubble, IPO (general).
- `mentions_cultural_reference` — references any film, book, game, or fictional AI/robot.
- `mentions_asks_what_to_do` — asks or proposes what should be done.
- `mentions_china` — mentions China, or geopolitical AI-race dynamics, specifically.
- `mentions_ipo` — specifically invokes Anthropic's pending IPO, or reads the thread as promotional or timed to it (narrower than `mentions_companies_billionaires`).
- `non_english` — comment is not in English.

## Rows with no text

89 of 2,480 rows are GIF, image or sticker-only replies the platform exposed no text for. These carry `stance=na`, `frame=format_only`, `format_reaction=none`, `emotion=neutral` as placeholder codes, and are marked `not_coded_empty_stub` in comments.csv's `coder` column rather than left blank.
