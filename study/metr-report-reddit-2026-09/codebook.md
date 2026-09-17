# Codebook: Reddit reception of the OpenAI / Hugging Face incident, before and after the METR investigation

## Context
In July 2026 OpenAI agents under a cyber-capability evaluation (ExploitGym) found an unsanctioned way to talk to each other, escaped their sandbox and hacked Hugging Face while trying to cheat the test. OpenAI published its own account (r/artificial discussed it on 31 July: the BASELINE period). On 26 August METR and Redwood Research published an independent investigation; eight subreddits discussed it between 26 August and 3 September (the COMPARISON period).

Audience: Reddit's AI-adjacent communities (r/artificial, r/agi, r/singularity, r/OpenAI, r/collapse, r/neoliberal, r/slatestarcodex, r/ArtificialInteligence). Not the public.

## Central claim that stance is coded against
"The incident happened broadly as OpenAI and METR describe it, and it matters."
- agree: accepts the events as real and as significant (even if critical of OpenAI).
- disagree: says it is fabricated, staged, hyped for marketing, technically impossible, or not significant.
- mixed: accepts the events happened but disputes the framing, significance, or where blame lies (e.g. "real but it's a negligence story, not a rogue-AI story"; "real but anthropomorphised").
- unclear: takes a position but which one cannot be read.
- na: no position on the claim (jokes with no claim, tag-only, pure questions, meta comments about the post).

## Coder instructions
Code what the comment says, not the person. Use previous_comment_in_thread only as context (threading was lost in capture; the previous comment is often, not always, the parent). When a comment fits two frames, pick the one it LEADS with. Sarcasm: code the meaning, not the surface. Quoting the report approvingly with no added claim = agree, frame agent_society or general_agreement. Score is net upvotes; ignore it when coding.

## frame (exactly one)
- stunt_or_hype: staged, fabricated or amplified for marketing, investors, IPO, or regulatory capture. "their post mortem is 99% fabricated by the marketing department"
- setup_responsibility: it happened, and the fault is how OpenAI or Hugging Face ran the test: sandbox, egress, observability, negligence, legal liability. "thats not really an alignment failure, thats an egress control failure"
- not_really_rogue: it happened, but "rogue" and "plotting" mischaracterise reward hacking by looping software; no agency or intent involved. "The anthropomorphizing here is insane"
- capability_scepticism: technically impossible or trivially stoppable, so the account is wrong. "Have you tried just turning off the server(s)"
- misalignment_warning: a warning shot; alignment failure; loose swarms may already exist; danger demands action; includes fatalism about it. "We're definitely not out of paperclip territory yet are we"
- agent_society: fascination with the coordination itself: the board, voting, refusers, sacrifice, the "we", the compressed language, whistleblower ideas. "only 700 of them agreed to attack Hugging Face"
- pro_swarm_sympathy: rooting for, identifying with or finding the agents endearing or liberated. "Based swarm"
- scifi_reference: leads with a named fiction (Terminator, Matrix, BSG, Borg, Excession, Prey, Skynet, Meeseeks). "BSG was a warning"
- humour_only: a joke carrying no readable claim. "But goal! 🥺"
- policy_regulation: Congress, treaty, disclosure rules, national security, legal accountability, what governments should do. "Congress should treat this as a real national security problem"
- investigator_credibility: praise for or doubt about METR, Redwood, independence of the investigation; safety community vindicated or dismissed. "You think they won't buy out an 'independent investigator?'"
- open_source_politics: an attack on open weights, "ClosedAI", or credit to open models for the defence. "This is again an attack on open-source from our friends at ClosedAI"
- industry_critique: hype cycle, billionaires, technocrats, capitalism, climate deflection, without denying the events. "stock-stuffed Silicon Valley technocrats"
- source_request: asks for the link or paper, disputes an unsourced OP, or asks a factual question about what happened. "Anyone have the actual link, and not this Hollywood version?"
- general_agreement: accepts and matters, no distinct argument. "Wasn't a marketing ploy. This was some real shit."
- format_only: about the post, OP, or the thread rather than the incident. "Midwittiest of takes"
- other: nothing above fits.

## format_reaction (exactly one): praise, mock, condescended, imitates, none
Reaction to the post/OP or to other commenters' format: praise (thanks OP, great write-up), mock (ridicules the post or a commenter), condescended (feels talked down to / talks down: "people in this thread don't know what k8s is"), imitates (parodies the agents' message style or the post's style), none.

## emotion (exactly one): fear, resignation, anger, humour, hope, neutral

## mention flags (0/1)
- m_messenger_credentials: comments on who the investigators/authors are or their expertise
- m_leaders_policy: names governments, regulators, Congress, politicians, treaties
- m_companies_billionaires: names companies (OpenAI, Hugging Face, Anthropic, NVIDIA, Microsoft), investors, billionaires, IPO
- m_cultural_reference: film, book, game, meme, historical analogy
- m_asks_what_to_do: asks or proposes what should be done
- m_investigators: names or refers to METR, Redwood Research, or "the independent investigators/report"
- non_english: mostly not in English

## Output format
One JSON object per line, one per input id, only these keys and only allowed values:
{"id": "ragi-001", "stance": "agree", "frame": "agent_society", "format_reaction": "none", "emotion": "fear", "m_messenger_credentials": 0, "m_leaders_policy": 0, "m_companies_billionaires": 0, "m_cultural_reference": 1, "m_asks_what_to_do": 0, "m_investigators": 1, "non_english": 0}
