# Findings note: MIT AI Risk Repository layer, Amanpour pilot

**Common Signals internal note, 28 September 2026. Pilot of an external taxonomy layer on the Amanpour Khlaaf study (amanpour-segment-2026-09, v3, 322 comments). Coded by Claude in one pass; not yet spot-checked.**

## Answer

The causal part of the MIT taxonomy earned its place on this thread. The domain part mostly did not.

Coding who commenters say caused the incident, and whether they think it was deliberate, split the accountability frame in a way the series' own codebook could not. Khlaaf's claim is negligence. Most of the people agreeing with her went further and said it was deliberate. Coding the risk domain mostly restated the stance split: domain 6 is the agree side, domain 7 is the disagree side.

## What was added

Three columns, with no existing code changed: risk_domain (the seven MIT domains, or none), cause_entity (human, ai, other, none) and cause_intent (intentional, unintentional, other, none), adapted from the MIT Causal Taxonomy. Timing was left out because the incident was a pre-deployment test, so timing doesn't vary between comments. Rules and tie-breaks are in codebook-extension.md. Source: Slattery et al., Patterns (2026), repository version 4 at airisk.mit.edu, CC BY 4.0.

## Results

Risk domain, all 322 comments: none 121 (38%), socioeconomic and governance (d6) 116 (36%), AI safety and failures (d7) 53 (16%), malicious use (d4) 20 (6%), privacy and security (d2) 11 (3%), human-computer interaction (d5) 1. Nobody raised discrimination or misinformation. Like-weighted, d6 carries 67% of all likes and d7 under 2%.

Domain tracks stance closely. 94 of the 116 d6 comments agree with Khlaaf; 29 of the 53 d7 comments disagree and only one agrees. Within this thread, domain mostly gives the two camps new labels. That is partly the thread's fault. Its central claim is an argument about which risk domain the incident belongs to, so a domain code was always going to line up with stance. A thread with a different central claim is the fairer test.

Attributed cause is where the new information is. Of the 151 comments agreeing with Khlaaf:

| Attributed cause | Comments | Share of agree |
| --- | --- | --- |
| Humans, deliberate | 67 | 44% |
| Humans, negligent | 28 | 19% |
| Humans, intent not stated | 18 | 12% |
| No attribution | 36 | 24% |
| Other | 2 | 1% |

Weighted by likes across the whole thread, the deliberate reading carries 40% of all likes and the negligence reading 7%. The top comment (134 likes, "Trying to sell us a solution to a problem they created") is a deliberate reading.

The accountability frame is where this matters most. It is the thread's dominant frame (73 comments, 55.5% of likes), and it contains both readings. Split by attributed cause: 32 comments call it deliberate (323 likes), 18 call it negligence (40 likes), 17 blame the company without saying which (214 likes). The frame list recorded agreement with Khlaaf. It could not record that most of that agreement was with a stronger and more cynical claim than hers: that OpenAI meant it, whether as a stunt, a sales pitch or by training agents to hack.

The disagree side is simpler: 26 of 40 attribute the incident to the AI (14 of them as deliberate scheming), and 12 make no attribution.

## Hypothesis for the message tests

Accountability framing of an AI incident may be heard as "they did it on purpose" more often than as "they were careless", and that reading may carry the engagement. If it holds, a systemic-accountability message (survey condition F0 = 2) could be buying agreement at the cost of feeding distrust, which a comprehension or attribution item after exposure could measure. One thread under one news segment is not evidence of that, only a reason to test it.

## Weaknesses

This is a single-pass LLM coding with no human review yet. Its weakest rule is that "they trained it to hack, so it hacked" counts as human and intentional. A reasonable reviewer could call much of that intent unstated instead, which would shrink the deliberate share. The spot-check sample oversamples exactly these rows for that reason.

The application rules were written by the coder immediately before coding. The categories are external, but the tie-breaks are not.

Eight endorsement replies inherit their parent's codes mechanically. One of them (a reply endorsing a sibling comment rather than its parent) probably inherited the wrong codes. The effect on any figure is under one point.

Domain was coded at the seven-domain level only. The d6 count lumps governance failure, competitive dynamics, jobs and power concentration together. In this thread it is mostly governance failure.

## Recommendation

Run the spot-check (spot-check-40.csv: 25 random rows plus 15 from the agree and human/intentional cell). If the cause codes hold at the series' usual 37 or 38 out of 40, adopt cause_entity and cause_intent as fixed dimensions across the series. Don't adopt risk_domain yet. Test it first on a study whose central claim is not itself about causes, such as the Soares reel or the Coxon thread. Only then decide whether it earns a column, and whether it belongs on the methodology page.

## Files

In the site repository at `_incoming/mit-taxonomy-pilot-2026-09/`: codebook-extension.md, coded_mit.csv (322 rows, the three new columns alongside id, stance, frame, likes and text), spot-check-40.csv (blank review columns), and this note as findings.md. Nothing in data/studies was changed and nothing is published.
