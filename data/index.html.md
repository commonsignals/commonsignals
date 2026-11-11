---
title: "Data"
url: "https://commonsignals.org/data/"
publisher: "Common Signals"
licence: "The coding and compilation are CC BY 4.0; comment text remains its authors'."
---

# Data

Every coded comment behind our reception studies, browsable and filterable, published under CC BY 4.0.

## YouTube comments on the Amanpour and Company Khlaaf segment

YouTube

Coded: 322

Positioned: 223

[Explore comments](https://commonsignals.org/data/amanpour-segment-2026-09/) [Read the article](https://commonsignals.org/problem-they-created-rogue-ai-agents-openai-huggingface-amanpour-khlaaf)

[study.json](https://commonsignals.org/data/studies/amanpour-segment-2026-09/study.json) · [codebook](https://commonsignals.org/data/amanpour-segment-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/amanpour-segment-2026-09/comments.csv)

**Changelog (version 3)**

- **v1**, 16 Sept 2026: Original coding of the second capture (322 comments, two parallel coders, 14 frames plus other), the run behind the published article's second-capture figures. Believed at the time not to have been archived as a row-level file; the article's method section and the project findings note were the only record.
- **v2**, 18 Sept 2026: Interim reconstruction, built from the raw yt-dlp export before the original coding file was located. Frame list redrafted from the article's own documented frames and quotes, aimed at reproducing the published figures rather than an independent read. It reproduced the structural counts exactly (322 rows, 232/90 top-level/reply split, 1,048 likes, 237 authors) but ran higher on agree share (72.7% vs 67.7% published) and lower on mixed (8.6% vs 14.3%), and under-counted messenger-credential mentions (3 of 322 vs the 7 then published). Ben Matthews spot-checked a random 40-comment sample of it, 40/40. Superseded by v3; figures taken from it should be discarded.
- **v3**, 18 Sept 2026: Restored from the genuine original coding file (coded.tsv, with coded_full.json and analysis.json), found in this repository's _incoming/ folder (files dated 17 September 2026). Same 322 comment IDs; stance, frame (15 values including other), format reaction (4 values), emotion and the six mention flags are exactly as the original run assigned them, with the six m_ flags renamed mentions_. Comment text is the file's anonymised text. Replaces v2 entirely. It matches the published article on every figure checked (the 223-comment stance base and its 67.7/17.9/14.3 split, like-weighted shares, frame and engagement shares, emotion among agreeing comments, regulation and US-administration mention rates, reply and top-level agree rates, top-comment like counts) except messenger-credential mentions: published as 7 (2.2%), 6 (1.9%) in this file. The article has been corrected to 6.

## YouTube comments on the Dwarkesh Podcast episode with Ajeya Cotra, "This might be the clearest warning shot we ever get"

YouTube

Coded: 2,999

Positioned: 1,590

[Explore comments](https://commonsignals.org/data/cotra-episode-2026-09/) [Read the article](https://commonsignals.org/clearest-warning-shot-openai-hugging-face-metr-cotra-dwarkesh)

[study.json](https://commonsignals.org/data/studies/cotra-episode-2026-09/study.json) · [codebook](https://commonsignals.org/data/cotra-episode-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/cotra-episode-2026-09/comments.csv)

**Changelog (version 2)**

- **v1**, 8 Sept 2026: Page capture, 1,249 of 1,569 comments, coded with an earlier frame list; article published from it. Files not archived.
- **v2**, 17 Sept 2026: Complete yt-dlp capture (2,999 comments) recoded against a redrafted 18-frame list with the series' full five-dimension scheme. Supersedes v1.

## X replies to Jacob Coxon's Anthropic resignation thread

X

Coded: 2,480

Positioned: 1,840

[Explore comments](https://commonsignals.org/data/coxon-resignation-2026-09/) [Read the article](https://commonsignals.org/coxon-resignation-x-analysis)

[study.json](https://commonsignals.org/data/studies/coxon-resignation-2026-09/study.json) · [codebook](https://commonsignals.org/data/coxon-resignation-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/coxon-resignation-2026-09/comments.csv)

**Changelog (version 1)**

- **v1**, 18 Sept 2026: Initial import: 2,480 rows from the coded TSV export, transformed into contract shape (columns renamed to the mentions_\<thing> convention, coder/spot_checked/correction_note columns added, parent_id/depth blanked since they do not resolve within this sample, reply_count and reposts kept as study-specific extra columns after correction_note, matching Cotra's reply_count precedent).

## Facebook comments on a 21-minute Diary of a CEO cut of the AI debate

Facebook

Coded: 2,075

Positioned: 1,366

[Explore comments](https://commonsignals.org/data/doac-clip-facebook-2026-09/) [Read the article](https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis)

[study.json](https://commonsignals.org/data/studies/doac-clip-facebook-2026-09/study.json) · [codebook](https://commonsignals.org/data/doac-clip-facebook-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/doac-clip-facebook-2026-09/comments.csv)

**Changelog (version 2)**

- **v1**, 7 Oct 2026: First release. A first pass under codebook v1 fell just short of the 90% reliability bar on stance (88.2%) and frame (88.8%). Codebook v2 defined unclear against na and added tie-breaks for debater_verdict and other; every row coded unclear, other or debater_verdict across the five DOAC studies (14,993 of 26,019) was recoded blind under it.
- **v2**, 9 Oct 2026: Corrected the artefact. Version 1 described this post as the 104-second Diary of a CEO clip of Nate Soares, published on 17 September 2026 (an assumed date). Checking the post showed it is "The REAL Reason AI Is Already Out Of Control", a 21:31 cut of the debate published on 21 September 2026. Title, artefact_title, artefact_published and notes updated; the comments and their codes are unchanged.

## Instagram comments on a two-minute Diary of a CEO clip of Nate Soares

Instagram

Coded: 77

Positioned: 38

[Explore comments](https://commonsignals.org/data/doac-clip-instagram-2026-09/) [Read the article](https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis)

[study.json](https://commonsignals.org/data/studies/doac-clip-instagram-2026-09/study.json) · [codebook](https://commonsignals.org/data/doac-clip-instagram-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/doac-clip-instagram-2026-09/comments.csv)

**Changelog (version 2)**

- **v1**, 7 Oct 2026: First release. A first pass under codebook v1 fell just short of the 90% reliability bar on stance (88.2%) and frame (88.8%). Codebook v2 defined unclear against na and added tie-breaks for debater_verdict and other; every row coded unclear, other or debater_verdict across the five DOAC studies (14,993 of 26,019) was recoded blind under it.
- **v2**, 9 Oct 2026: Corrected the artefact. Version 1 described this post as the 104-second Diary of a CEO clip of Nate Soares, with an assumed post date of 17 September 2026. Checking the post showed it is a 2:09 clip led by Soares, published on 17 September 2026 (now verified), and the same cut as the TikTok post; the 104-second YouTube Short is a different video. Title, artefact_title and notes updated; the comments and their codes are unchanged.

## YouTube Shorts comments on the Diary of a CEO trailer for its AI debate

YouTube Shorts

Coded: 261

Positioned: 171

[Explore comments](https://commonsignals.org/data/doac-clip-shorts-2026-09/) [Read the article](https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis)

[study.json](https://commonsignals.org/data/studies/doac-clip-shorts-2026-09/study.json) · [codebook](https://commonsignals.org/data/doac-clip-shorts-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/doac-clip-shorts-2026-09/comments.csv)

**Changelog (version 2)**

- **v1**, 7 Oct 2026: First release. A first pass under codebook v1 fell just short of the 90% reliability bar on stance (88.2%) and frame (88.8%). Codebook v2 defined unclear against na and added tie-breaks for debater_verdict and other; every row coded unclear, other or debater_verdict across the five DOAC studies (14,993 of 26,019) was recoded blind under it.
- **v2**, 9 Oct 2026: Corrected the artefact. Version 1 described this post as the 104-second Diary of a CEO clip of Nate Soares, posted to four platforms. Checking the transcript and frames showed it is a trailer for the full debate, a montage of the host and all four panellists in which Soares has one line, and a different video from the TikTok, Instagram and Facebook posts. Title, artefact_title and notes updated; the comments and their codes are unchanged.

## TikTok comments on a two-minute Diary of a CEO clip of Nate Soares

TikTok

Coded: 50

Positioned: 27

[Explore comments](https://commonsignals.org/data/doac-clip-tiktok-2026-09/) [Read the article](https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis)

[study.json](https://commonsignals.org/data/studies/doac-clip-tiktok-2026-09/study.json) · [codebook](https://commonsignals.org/data/doac-clip-tiktok-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/doac-clip-tiktok-2026-09/comments.csv)

**Changelog (version 2)**

- **v1**, 7 Oct 2026: First release. A first pass under codebook v1 fell just short of the 90% reliability bar on stance (88.2%) and frame (88.8%). Codebook v2 defined unclear against na and added tie-breaks for debater_verdict and other; every row coded unclear, other or debater_verdict across the five DOAC studies (14,993 of 26,019) was recoded blind under it.
- **v2**, 9 Oct 2026: Corrected the artefact. Version 1 described this post as the 104-second Diary of a CEO clip of Nate Soares. Checking the post showed it is a 2:08 clip led by Soares, published on 17 September 2026, and the same cut as the Instagram post; the 104-second YouTube Short is a different video. Title, artefact_title and notes updated; the comments and their codes are unchanged.

## YouTube comments on the Diary of a CEO AI debate episode

YouTube

Coded: 23,794

Positioned: 15,928

[Explore comments](https://commonsignals.org/data/doac-debate-youtube-2026-09/) [Read the article](https://commonsignals.org/cant-we-just-unplug-it-doac-ai-debate-comment-analysis)

[study.json](https://commonsignals.org/data/studies/doac-debate-youtube-2026-09/study.json) · [codebook](https://commonsignals.org/data/doac-debate-youtube-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/doac-debate-youtube-2026-09/comments.csv)

**Changelog (version 1)**

- **v1**, 7 Oct 2026: First release. A first pass under codebook v1 fell just short of the 90% reliability bar on stance (88.2%) and frame (88.8%). Codebook v2 defined unclear against na and added tie-breaks for debater_verdict and other; every row coded unclear, other or debater_verdict across the five DOAC studies (14,993 of 26,019) was recoded blind under it.

## Reddit reception of the OpenAI and Hugging Face incident, before and after the METR investigation

Reddit

Coded: 516

Positioned: 395

[Explore comments](https://commonsignals.org/data/metr-report-reddit-2026-09/) [Read the article](https://commonsignals.org/openai-and-shut-metr-hugging-face)

[study.json](https://commonsignals.org/data/studies/metr-report-reddit-2026-09/study.json) · [codebook](https://commonsignals.org/data/metr-report-reddit-2026-09/codebook/) · [comments.csv](https://commonsignals.org/data/studies/metr-report-reddit-2026-09/comments.csv)

**Changelog (version 1)**

- **v1**, 17 Sept 2026: Recode of the raw page captures with the series' full five-dimension scheme. Supersedes the coding run behind the published article, which is not on file. Counts differ from the article (516 coded here against 692 reported) because collapsed replies in the captures were not expanded.
- **v1**, 17 Sept 2026: Spot-check recorded: 40/40.
- **v1**, 23 Sept 2026: The article now reports this dataset's counts (516 coded, 395 positioned). The discrepancy noted on 17 September no longer applies.

## Instagram comments on Nate Soares's reel "We stop AI. You help?"

Instagram

Coded: 2,136

Positioned: 1,271

[Explore comments](https://commonsignals.org/data/soares-reel-2026-08/) [Read the article](https://commonsignals.org/ai-risk-reel-analysis-nate-soares-miri)

[study.json](https://commonsignals.org/data/studies/soares-reel-2026-08/study.json) · [codebook](https://commonsignals.org/data/soares-reel-2026-08/codebook/) · [comments.csv](https://commonsignals.org/data/studies/soares-reel-2026-08/comments.csv)

**Changelog (version 2)**

- **v1**, 29 Aug 2026: Logged-in API capture, 1,666 of 1,703 comments, coded with like counts available. Article published from it.
- **v2**, 17 Sept 2026: Page-text recapture (2,136 of 2,715 comments then live; likely under-counts unexpanded reply threads, the same limitation seen in the METR Reddit capture) recoded against an 18-frame list. No like counts available in this capture, so engagement-weighted findings from v1 cannot be reproduced or updated. Supersedes v1 for stance/frame shares only.

Each study is coded on stance, frame, format reaction and emotion against its own codebook, plus a handful of flags for what a comment mentions. Stance and emotion use mostly the same categories across studies; frame and format reaction are study-specific. Comment text is verbatim; author identities are hashed, not published. Full contract, JSON schemas and licensing: [/data/studies/README.md](https://commonsignals.org/data/studies/README.md). The coding and compilation are CC BY 4.0; comment text remains its authors'.
