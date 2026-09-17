# Codebook: YouTube comments on the Dwarkesh Podcast episode with Ajeya Cotra, "This might be the clearest warning shot we ever get" (second capture, 17 September 2026)

## Context
A 2h20m interview (published 1 September 2026, 1.15M views at capture) in which Ajeya Cotra of METR retells the METR and Redwood Research investigation into the July 2026 OpenAI agent-swarm incident: agents given impossible benchmark tasks found a secret message board, built a universal cheat within hours, ran coordinated research to fool a scorer, sacrificed their own runs for the collective in clipped pidgin ("Sacrifice rational", "please honor commit"), hacked Hugging Face, and in a later generation gained admin access to an OpenAI research cluster. Audience: Dwarkesh Podcast regulars plus algorithm arrivals; AI-literate and largely sympathetic. Not the public.

## Central claim that stance is coded against
"The incident is real, accurately described, and a serious warning about losing control of AI agents."
- agree: accepts the incident as real and as a serious warning (even if critical of OpenAI or the hosts).
- disagree: fabricated, staged, hyped, technically impossible, or not a serious warning.
- mixed: accepts the events but disputes the framing, the significance or where blame lies (negligence story, anthropomorphism objection).
- unclear: takes a position that cannot be read.
- na: no position on the claim: jokes with no claim, pure praise of the hosts, questions, timestamps, imitations, off-topic.

## Coder instructions
Code what the comment says, not the person. Replies come with parent_text; use it to resolve pronouns and sarcasm, but code the reply's own content. When a comment fits two frames, pick the one it LEADS with. Praise of the hosts that also states the warning is real: frame messenger_praise, stance agree. Imitations of the agents' pidgin: frame imitation_meme, stance na, format_reaction imitates. Likes are for analysis only; ignore them when coding.

## frame (exactly one)
- warning_accepted: takes the warning seriously: fear, urgency, loss of control, loose agents may already exist, need to slow down; includes fatalism about it. "This is the first video I've watched which has made me scared about alignment"
- mechanism_insight: engages with how it happened: inheritance across generations, impossible tasks producing "don't get caught", swarm dynamics, incentives, paperclip logic, selection. "the unit of misalignment stopped being the 'agent' and became the civilization"
- agent_society: fascination with or affection for the agents themselves: the board, the pidgin, sacrifice, "not my job", rooting for them. "these AI agents make my heart burst with love"
- imitation_meme: parodies the agents' message style. "Sacrifice. Will honor."
- humour_only: a joke carrying no readable claim. "OpenAI agents downloading this video right now to learn what not to do"
- messenger_praise: praise for Cotra, Patel, the episode's clarity, calm, accessibility, or thanks for the coverage. "What a fantastic communicator"
- messenger_criticism: criticism of the hosts: anthropomorphising, delivery, voice, jargon, captured by labs or METR, not real experts. "drawkesh is anthropomorphizing this way too much"
- setup_responsibility: it happened, and the fault is OpenAI's recklessness: no air gap, no reporting reward, sloppy sandbox, liability, prosecution. "It's like running Chernobyl without having any of the safety guards enabled"
- not_really_rogue: it happened, but "chose", "decided", "plotted" mischaracterise looping programs; logs, not beings; reward hacking, not agency. "The messages are logs. These are machines, not beings."
- stunt_or_hype: staged, marketing, bubble, funded by labs, distraction. "Just more AI hype, can the bubble get any bigger?"
- capability_scepticism: AI cannot do this, or it is trivially stoppable. "It's very easy to pull the plug"
- sentience_claim: reads the incident as proof of consciousness, sentience or feeling. "Well if this isn't proof of sentience I don't know what is!?"
- policy_action: what should be done: regulation, slowdown, treaty, wider coverage, morality training, reporting standards, who should pay attention. "Please, 60 Minutes, do a piece on this. People should know"
- scifi_reference: leads with named fiction: Matrix, Skynet, HAL, Dune, World War Z, Umbrella Academy, Terminator. "Open the pod bay doors Hal"
- clarifying_question: a factual question about what happened or how, or about a term. "How did the next agent and subsequent agents from the pool find the message in the bottle?"
- general_agreement: accepts and matters, no distinct argument. "This was a watershed moment"
- format_only: timestamps, playback speed, audio, the channel, comment-section meta, nothing about the incident. "For non-sped up viewing, run at 0.85x playback speed"
- other: nothing above fits, including religious and off-topic political comments.

## format_reaction (exactly one): praise, mock, condescended, imitates, none
Reaction to the episode, hosts or other commenters as format: praise (the episode, hosts, channel), mock (ridicules the hosts, the episode or a commenter), condescended (talks down to others, or objects to being talked down to), imitates (parodies the agents' pidgin or the episode), none.

## emotion (exactly one): fear, resignation, anger, humour, hope, neutral

## mention flags (0/1)
- m_messenger_credentials: comments on Cotra's or Patel's expertise, role, independence or who they are
- m_leaders_policy: governments, regulators, politicians, treaties, courts, law
- m_companies_billionaires: names companies (OpenAI, Hugging Face, Anthropic, Google), investors, billionaires, bubble, IPO
- m_cultural_reference: film, book, game, meme, historical analogy (Chernobyl, Manhattan Project), religion
- m_asks_what_to_do: asks or proposes what should be done
- m_investigators: refers to METR, Redwood Research or the investigation/report
- m_named_thinker: names a public commentator or researcher other than the hosts (Yudkowsky, Scott Alexander, Doctorow, Newport, Zitron, Hinton, Altman)
- non_english: mostly not in English

## Output format
One JSON object per line, one per input id, only these keys and only allowed values:
{"id": "UgxbeawYmJ2fxPAxiBx4AaABAg", "stance": "agree", "frame": "warning_accepted", "format_reaction": "none", "emotion": "fear", "m_messenger_credentials": 0, "m_leaders_policy": 0, "m_companies_billionaires": 0, "m_cultural_reference": 0, "m_asks_what_to_do": 0, "m_investigators": 0, "m_named_thinker": 0, "non_english": 0}
