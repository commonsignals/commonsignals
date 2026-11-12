---
title: "Methodology"
url: "https://commonsignals.org/methodology"
published: 2026-09-16
updated: 2026-11-11
publisher: "Common Signals"
---

# Methodology

Last updated: 11 November 2026

Common Signals studies how the people who see messages about AI respond to them. Our [theory of change](https://commonsignals.org/theory-of-change) explains how this work fits our wider aims. This page describes the method our studies share, so anyone can check, criticise or repeat the work. Each study publishes its own figures, codebook and dataset.

## What our studies can and can't tell you

Each study takes one piece of AI communication, such as a video, post, report or thread, and codes the comments people left under it. We report who accepted its central claim, which frames they used, how they reacted to the format and the messenger, and their emotional register.

Comment threads are self-selected samples, not samples of the public. Commenters choose to comment, platforms decide which comments get seen, and the people who watched and moved on leave no trace. A study describes one audience's reaction to one piece of communication. We use the results to generate specific, testable hypotheses for message testing with representative samples, which is the work Common Signals exists to do.

Some studies compare two moments, for example reactions before and after an independent party checked a claim. These natural experiments can say something about change. The audience usually changes along with the evidence, though, so we treat the direction as the finding and the exact figures as approximate.

## How a study works

### 1. Collecting comments

We use the most complete route each platform allows, and report how many comments we retrieved against the platform's own count.

- YouTube: a full comment export with threading and like counts.
- Instagram: the platform's comment API, called from a logged-in browser session.
- Reddit: page captures. Collapsed replies aren't always expanded, so deep threads can be under-sampled.
- X: we don't use X's paid API. We read the reply feed in a signed-in browser across every sort order. Each view stops loading after a few hundred replies, so on large threads we see only the slice X's ranking shows.

Before any comment is collected, the artefact itself is checked and recorded from the platform: its URL, title or caption, running length and post date, read from the platform's own player or metadata (yt-dlp's info.json for YouTube; the player, oEmbed data or the post ID elsewhere), and who appears in it, checked from the transcript or from frames taken through the video. Where posts on several platforms are treated as one artefact, each is checked on its own, and a study calls them the same cut only if title, length and speakers all match. These details go into the study record at capture and are never filled in later by assumption.

This check was added in October 2026, after the Diary of a CEO debate studies. The Facebook post assumed to be a 104-second clip of Nate Soares turned out to be a 21-minute cut of the debate, posted four days after the episode. The TikTok and Instagram posts were the same two-minute Soares cut, and the YouTube Short was a 104-second trailer for the whole debate. The article built on the assumption compared different videos as if they were one clip. It was taken down, and the study records were corrected with a changelog entry for each.

We remove ads and the author's own posts before coding. Before any data leaves the collection environment, usernames are replaced with salted one-way hashes, and @handles inside comments become @user. We quote comments word for word, spelling included, and never publish usernames, in line with research ethics guidance on social media data from Townsend and Wallace (2016).

### 2. Building the codebook

Every comment is coded on the same five dimensions:

- stance towards the piece's central claim: agree, disagree, mixed, unclear or not applicable
- frame: the main way the commenter makes sense of the issue
- reaction to the format: praise, mockery, feeling talked down to, imitation, or none
- emotional register: fear, resignation, anger, humour, hope or neutral
- a few yes/no flags, such as whether the comment mentions the messenger or asks what to do

Stance, format and emotion use the same categories in every study, so they can be compared across [our studies](https://commonsignals.org/research). Frames are drafted for each piece from 150 random comments plus the 50 most engaged. We follow [Robert Entman's (1993) definition of a frame](https://doi.org/10.1111/j.1460-2466.1993.tb01304.x): the aspects of an issue a message selects and emphasises to define the problem, its cause and what should be done about it. Each frame gets a definition and a verbatim example.

We write down the central claim that stance is coded against. If a piece argues against an earlier account, agree means accepting its reframing. A person approves the frame list before any coding starts.

### 3. Coding

[Claude](https://www.anthropic.com/claude), a large language model made by Anthropic, codes every comment in parallel batches against the written codebook. For replies, it also sees the comment being replied to. Language models can [match or beat trained crowd workers on annotation tasks like this](https://doi.org/10.1073/pnas.2305016120) (Gilardi, Alizadeh and Kubli, 2023). They can also drift from the codebook over long batches, overuse catch-all categories and misread irony.

We check the output in two ways. Software confirms that every code comes from the allowed list and that every comment is coded exactly once. A person then spot-checks a random sample of 40 comments against the codebook, and each study publishes the result, except the Amanpour and Company study, whose result was not recorded. The Diary of a CEO study was checked by a blind second coding instead, described under limitations. Where a heavily liked comment affects the engagement-weighted results, we review its codes individually and note any correction.

A 40-comment check is thin evidence. That's why we report percentages as whole numbers and treat them as accurate to within a few points.

### 4. Analysis

Scripts compute every figure from the coded dataset. Each study states the base for its stance percentages, usually the comments taking a readable position. Every quote in an article is matched word for word against the dataset before publication.

We report two kinds of share. Comment shares count each comment once, whether it got no likes or thousands. Engagement-weighted shares weight each comment by its likes or upvotes. Likes show what the platform surfaced and people noticed, not what changed anyone's mind, and a handful of comments usually hold most of them. So we report both.

## Limitations

In order of importance:

1

The sample is self-selected and ranked by the platform, as described above.

2

Coding is done by one model. The newest study, on the Diary of a CEO debate, has a blind second coding: a random sample of 347 comments was coded a second time by a separate run of the same model, and the two agreed on stance for 91% (Cohen's kappa 0.87) and on frame for 89% (kappa 0.87). Because both runs used the same model, they can share the same mistakes. The five earlier studies were checked by one person on a sample of 40 and have no second coder, so no agreement figure.

3

Comparing studies changes several things at once: audience, platform, messenger and message. Our research can suggest that framing affects reception. It can't separate framing from audience.

4

Silence is weak evidence. A comment that doesn't mention a risk, a messenger or a policy hasn't said it doesn't matter. Mention flags show what people chose to raise.

5

Where we couldn't watch a piece directly, we reconstructed its argument from the transcript or from what commenters repeated, and the study says so.

Our closing advice sometimes draws on established research, such as [Kim Witte's (1992) work on fear appeals](https://doi.org/10.1080/03637759209376276), which finds that threat messages persuade when people believe they can act and backfire when they can't. Communication researchers call that belief efficacy. We cite that research where we use it. What our studies add is comparable evidence of how specific AI messages are received.

## What we're adding

Several of these changes follow the method used by the [AI Dialogue Report](https://aidialoguereport.org/findings/).

- More than one coder. The Diary of a CEO study took a first step, with a blind second coding of a random sample by a separate run of the same model. Models from different developers make different mistakes, so we plan to code each comment with more than one model, accept the codes they agree on and send disagreements to an arbiter, which gives every study an agreement figure to publish. We also plan a blind second coding of the five earlier studies.
- Quote-backed codes. Each code will cite the words in the comment that support it, and software will check the words are there.
- A larger human benchmark. A bigger hand-coded sample will let us report precision and recall for each category, and correct published shares for the measured error rate using the [Rogan-Gladen method](https://doi.org/10.1093/oxfordjournals.aje.a112510) (Rogan and Gladen, 1978).
- Corrections for multiple comparisons. When we compare many groups, such as stance across every frame, some differences will look real by chance. We will report only those that survive a [Benjamini-Hochberg false discovery rate correction](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) (Benjamini and Hochberg, 1995).
- Shared categories where good taxonomies exist. Where commenters name specific AI risks, we will code them against the [MIT AI Risk Repository](https://arxiv.org/abs/2408.12622) (Slattery et al., 2025), alongside the frames drawn from each thread.
- A closer human read. In every study, a person will read the 100 most-liked comments and every comment coded mixed.

## Data and contact

Each study's codebook and coded dataset are published with it. Terms used here are defined in our [glossary](https://commonsignals.org/glossary). We want to hear about errors, recoding and criticism of the method: [hello@commonsignals.org](mailto:hello@commonsignals.org).

## References

- Benjamini, Y. and Hochberg, Y. (1995). [Controlling the false discovery rate: a practical and powerful approach to multiple testing](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x). Journal of the Royal Statistical Society, Series B 57(1), 289-300.
- Entman, R. M. (1993). [Framing: toward clarification of a fractured paradigm](https://doi.org/10.1111/j.1460-2466.1993.tb01304.x). Journal of Communication 43(4), 51-58.
- Gilardi, F., Alizadeh, M. and Kubli, M. (2023). [ChatGPT outperforms crowd workers for text-annotation tasks](https://doi.org/10.1073/pnas.2305016120). Proceedings of the National Academy of Sciences 120(30), e2305016120.
- Rogan, W. J. and Gladen, B. (1978). [Estimating prevalence from the results of a screening test](https://doi.org/10.1093/oxfordjournals.aje.a112510). American Journal of Epidemiology 107(1), 71-76.
- Slattery, P. et al. (2025). [The AI Risk Repository: a comprehensive meta-review, database, and taxonomy of risks from artificial intelligence](https://arxiv.org/abs/2408.12622). arXiv:2408.12622.
- Townsend, L. and Wallace, C. (2016). Social media research: a guide to ethics. University of Aberdeen.
- Witte, K. (1992). [Putting the fear back into fear appeals: the extended parallel process model](https://doi.org/10.1080/03637759209376276). Communication Monographs 59(4), 329-347.
