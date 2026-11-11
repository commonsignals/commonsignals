# Codebook: YouTube comments on the Amanpour and Company Khlaaf segment (second capture, 16 September 2026; restored original coding)

## Provenance
This is the codebook for the original second-capture coding of this thread, restored on 18 September 2026 from the original coding file. It replaces an interim reconstruction (v2) built earlier the same day before that file was located. The original coder brief was not archived with the file, so the definitions and examples below were written afterwards from the frame names and the coded comments: they describe how the codes were applied, not the wording the coders were given. The frame list is the one the original run used (15 values, including other) and is drafted for this thread, so frame-level figures are not comparable with other studies' frames. Stance, format reaction and emotion use the series' shared categories.

## Context
Source: comments on "What Really Happened When OpenAI Bots Escaped a Cybersecurity Test?" (Amanpour and Company, YouTube, published 3 September 2026). A 13-minute PBS interview: Hari Sreenivasan with Heidy Khlaaf, chief AI scientist at the AI Now Institute and a former OpenAI safety engineer. Her argument: the "machines went rogue" framing is wrong and a distraction; the real story is corporate negligence and hype, a company ran a negligent test and gave its agents the access that made the breakout possible. Audience: a mainstream, PBS-skewed news audience. Not the public.

## Central claim that stance is coded against
"The real story of the OpenAI agent-swarm incident is corporate negligence and hype, not a machine going rogue."
- agree: accepts Khlaaf's reframing: the real story is corporate negligence and hype, not a machine going rogue.
- disagree: rejects the reframing and defends the rogue or dangerous-AI account, including the objection from the AI-safety side that she understates what the swarm did, or dismisses her account outright.
- mixed: accepts part of the reframing and rejects or reframes part.
- unclear: engages with the incident but the position cannot be read.
- na: no position on the central claim: jokes, reactions, questions, remarks about the production, tangents.

## Coder instructions
The original coder brief was not archived with the coding file, so this text does not reproduce it. It records the conventions the coded output is consistent with, written on 18 September 2026 from the coded comments themselves. Stance is coded against the central claim: a comment that takes no readable position on it is na, and one that engages with the incident but whose position cannot be read is unclear. Every comment carries exactly one frame, one format reaction and one emotion, the dominant one; frame is the point the comment leads with. Mention flags are independent yes/no marks and can accompany any frame. Flags are judgement calls, not keyword matches: 3 of the 8 comments that name Hugging Face are not flagged mentions_hugging_face, so flag counts are lower bounds on keyword mentions. Definitions and examples in this codebook describe how the codes were applied; they are not the wording the coders were given.

## frame (exactly one)
- accountability: the real problem is corporate negligence, choices or incentives (OpenAI, its executives, the AI industry), not machines acting on their own; echoes Khlaaf's reframing, or calls out or blames the companies. "Behind every 'rogue' AI, is a wizard of Oz type rogue human."
- regulation: calls for or discusses regulation, a watchdog, legislation, prosecution or government oversight of AI companies. "A new "Watchdog" agency is needed for all of this."
- us_politics: reads the incident through American politics: the current US administration or its officials as the reason nothing will be done, elections, party politics. "In any other administration OpenAI would be investigated and prosecuted. This is irresponsible criminal conduct."
- hype_staged: dismisses the incident or the segment as staged, exaggerated, a publicity stunt, marketing or stock manipulation. "Smells like a publicity stunt to me."
- warning_shot_dispute: disputes Khlaaf's account from the AI-safety side: says she understates or misdescribes what the swarm did, that the agents showed intent, scheming or coordination, or that this really was a dangerous-AI event. "They don't have intent? Are you blind? This hack was a whole series of intent chained together."
- anti_anthropomorphism: objects to describing the agents as autonomous, sentient or 'escaping'; they only did what they were programmed and instructed to do. ""AI" is NOT AUTONOMOUS. "It" does not "escape" and it does not "think"."
- existential_dread: fear, fatalism or doom about AI itself (loss of control, being wiped out) without engaging Khlaaf's argument. "Oh boy, first official espionage task. I don’t think we are driving this truck anymore."
- analogous_crisis: compares the incident to another failure of corporate or institutional accountability (an unlocked bank vault, Equifax, LifeLock, lab leak, gain-of-function research). "What if a bank "tested" what would happen if it left it's vault unlocked and it's doors open all night in a busy city?"
- credential_contested: argues about who Khlaaf is: her OpenAI background, funding, independence or expertise, attacking or defending her (the flag mentions_messenger_credentials marks any such mention, whatever the frame). "Oh shes a very good AI PR person"
- hostile_dismissal: dismisses or attacks Khlaaf or the segment with open hostility, without naming a credential or making an argument. "Why should I trust this woman?"
- praise_guest: praise for Khlaaf, the interview or the programme is the main content of the comment: clarity, expertise, calm. "EXACTLY the guest needed for this story!"
- geopolitical_race: frames AI as a race between countries (China, Russia), so that guardrails are unlikely or unwise. "The trouble is no country wants to put guards rails up if their competition is operating without guardrails"
- pop_culture_ref: leads with a fictional or cultural reference: Frankenstein, Star Trek, science fiction. "Mary Shelley’s Frankenstein runaway is where we are headed."
- offtopic_meta: about the video or the thread rather than the incident: captions, sound, the guest's appearance or speaking pace, banter with other commenters. "The sound quality is superb."
- other: nothing above fits, including on-topic remarks with no distinct argument, reactions too short to read, and unrelated tangents. "Fun fact: parrots have been known to speak human language."

## format_reaction (exactly one): praise, mock, condescended, none
Reaction to the segment, the guest or other commenters as format: praise (praises the interview, the guest or the programme); mock (ridicules or sneers at the guest, the segment or another commenter); condescended (talks down to the guest or others, or objects to being talked down to; in this thread mostly remarks that the guest speaks too fast); none (no reaction to the segment as a format).

## emotion (exactly one): fear, resignation, anger, humour, hope, neutral
Dominant emotional register: fear (fear, alarm or dread); resignation (fatalism, weariness, a sense that nothing can be done); anger (anger, outrage or contempt); humour (joking, sarcasm played for laughs, laughing emoji); hope (gratitude, admiration or optimism); neutral (no dominant emotion; a level tone).

## mention flags (true/false)
- m_messenger_credentials: comments on Khlaaf's expertise, experience, employer, funding or affiliations, including her former OpenAI role, attacking or defending her
- m_leaders_policy: governments, regulators, politicians, Congress, laws or regulation, prosecution, oversight or a watchdog
- m_administration_politics: the current US administration, its officials or American party politics, typically as the reason nothing will be done
- m_hugging_face: refers to Hugging Face, the platform the agents breached, or to what it said or did
- m_other_coverage: refers to other coverage or reports of the incident, such as the Atlantic, CNN, OpenAI's own report or the METR and Redwood Research investigation
- m_named_individual: names a specific person other than the guest: the host, AI-company executives such as Sam Altman, or politicians and regulators
- No non_english flag: the original run did not code one.

## From the original file to comments.csv
The original file was coded.tsv. Its columns map to comments.csv as follows; nothing was recoded.
- engagement is likes; created_at is published_at (UTC, written with a trailing Z); reply_count is unchanged.
- the six m_ flag columns are renamed mentions_ (m_messenger_credentials to mentions_messenger_credentials, and so on) and their 0/1 values written as false/true.
- text is the anonymised text from coded.tsv (@handles replaced with @user), with its escaped newlines restored.
- author_hash, published_at and every coded value are the original file's; the author hashes and timestamps differ from the superseded v2 file's.
- the coder, spot_checked and correction_note columns are added to match the other studies; spot_checked is false throughout because the sampled rows were not recorded.
