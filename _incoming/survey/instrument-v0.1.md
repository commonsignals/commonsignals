# Common Signals: survey instrument for Britain Talks AI and America Talks AI

Draft v0.1, 24 September 2026. Prepared for internal review and for
fieldwork partner scoping. Not yet pre-registered.

Adapted from the "AI RCT UK 2026" instrument (supplementary materials).
That study was a randomised vignette experiment testing whether reading
about a single AI risk area shifts concern and willingness to act. This
instrument keeps its consent language, its core attitude and
civic-action items and its emotion and timing measures, and rebuilds the
rest around Common Signals' purpose: a values-segmented dataset of how
the British and American publics relate to AI, which messages shift
understanding within each segment, and which messengers each segment
already trusts.

## How to read this document

Text the respondent sees is written in plain paragraphs. Design and
programming notes for the research team appear in highlighted boxes and
are never shown to respondents. Where the UK and US versions differ,
both are given and marked [UK] and [US]. Everything else is shared
so the two datasets can be compared item for item.

Response formats: single choice, select all that apply, grids are
one row per statement.

Item codes in brackets, for example [A1], are for the codebook and
analysis plan. Codes are stable across the UK and US versions.

## Design summary

| Element       | Specification |
|---------------|----------------|
| Population    | [UK] Adults 18+ resident in the United Kingdom. [US] Adults 18+ resident in the United States. |
| Sample        | Flagship target n = 2,000 per country, quota sampled to national population on age, gender, region and education, with weighting to census benchmarks. Pilot-scale fieldwork (n = 1,000 to 2,000) uses the same instrument with a shortened message module. |
| Mode          | Online panel, self-completion. Panel ID auto-captured. |
| Length        | Target median 15 minutes. Modules A to D and I to K are asked of everyone. Module F randomises message exposure. Hard cap at 20 minutes for any single path; cut the named-messenger grid (G2) first if the pretest runs long. |
| Segmentation  | Values and worldview battery (Module C) analysed by latent class analysis to produce a segment solution of roughly five to seven groups. Segments are derived from values items only; AI attitude items are outcome variables and are never used to define segments. |
| Message test  | Between-subjects. Each respondent sees one message from a balanced set (present-day harms, longer-term risk, benefit-led, bridging) or a neutral control passage, then answers a common post-exposure block. Analysis compares outcomes by message within segment. |
| Messenger map | Two-part trust battery: messenger types (everyone) and named messengers drawn from the Common Signals messenger map (country-specific list of 12 to 15). |
| Outputs       | Anonymised respondent-level dataset, codebook, segment allocation file and pre-registered analysis plan, published under CC BY 4.0 at commonsignals.org/data/. |
| Ethics        | Anonymous, no identifiers stored beyond the panel ID needed for payment, which is deleted after fieldwork closes. Independent ethics review before pre-registration. |

Design note: the values battery in Module C is an original draft written
for this instrument. The strategy is to use a licensed version of the
More in Common core beliefs battery for the US wave if agreement is
reached, so that segments can be compared with Hidden Tribes. If
licensed, Module C is replaced wholesale and the rest of the instrument
is unchanged. For the UK, check whether the Britain Talks Climate
segmentation items can be reused under agreement with Climate Outreach
and More in Common before fielding an original battery. Do not field two
different batteries in the two countries unless a crosswalk is agreed in
the analysis plan.

## Module A: introduction and consent

### A0. Introduction

Thank you for taking part in this survey about artificial intelligence.
Artificial intelligence (AI) refers to computer systems that can perform
tasks previously thought to need human intelligence, such as
understanding language, making decisions and recognising complex
patterns.

The survey takes about 15 minutes. There are no right or wrong answers.
We want to know what you think, whatever your level of interest in the
subject.

### A1. Consent

What is involved: you will answer questions about your views on a range
of topics, read one short text, and answer questions about it.

Your rights: taking part is voluntary. You can stop at any time by
closing the window. Your answers are anonymous and no identifying
information is collected beyond your panel ID, which is used only to
arrange your payment and is deleted when the study closes.

Risks and benefits: there are no anticipated risks beyond those of
everyday life. Your answers help build a public, freely available
picture of how people in [UK: the UK / US: the United States] think
about AI.

Data use: anonymised data will be published openly so that researchers,
journalists and organisations can use it. No individual can be
identified from the published data.

Who is running the study: Common Signals, an independent, non-partisan
research organisation. Questions can be sent to hello@commonsignals.org
or via the panel messaging system.

By clicking "I agree" you confirm you are 18 or over and consent to take
part. [A1]

- I agree
- I do not agree [terminate]

### A2. Panel ID

Your panel ID [A2]

This should fill in automatically.

## Module B: screening and quotas

B1. What is your age? [B1]

[Numeric entry. Terminate if under 18. Quota bands: 18-24, 25-34,
35-44, 45-54, 55-64, 65+]

B2. How do you describe your gender? [B2]

- Man
- Woman
- In another way
- Prefer not to say

B3 [UK]. Where in the UK do you live? [B3]

East of England / East Midlands / London / North East / North West /
Northern Ireland / Scotland / South East / South West / Wales / West
Midlands / Yorkshire and the Humber

B3 [US]. In which state do you live? [B3]

[Dropdown of 50 states plus District of Columbia. Recode to the four
Census regions (Northeast, Midwest, South, West) and nine divisions for
quotas and reporting.]

B4. Which of these best describes the area where you live? [B4]

- A large city
- A suburb or the outskirts of a city
- A town
- A village or rural area

B5. What is the highest level of education you have completed? [B5]

[UK]

- No formal qualifications
- GCSEs, O-levels or equivalent
- A-levels, BTEC, Highers or equivalent
- Vocational or trade qualification
- Undergraduate degree
- Postgraduate degree

[US]

- Less than high school
- High school graduate or GED
- Some college, no degree
- Associate degree
- Bachelor's degree
- Graduate or professional degree

Programming note: quotas on B1, B2, B3 and B5 are set to national census
benchmarks. Close quota cells as they fill. Remaining demographics are
asked in Module J so that the survey opens with the questions it exists
for.

## Module C: values and worldview

This section is about your views on life and society in general, not
about AI. There are no right or wrong answers.

C1. How much do you agree or disagree with each of the following
statements? [C1_01 to C1_20]

[Grid. Scale: Strongly disagree / Somewhat disagree / Neither agree nor
disagree / Somewhat agree / Strongly agree. Randomise item order.
Present in two screens of ten.]

| Code  | Statement | Dimension (not shown) |
|-------|-----------|------------------------|
| C1_01 | Most people can be trusted. | Social trust |
| C1_02 | People who run big institutions such as governments, large companies and the media generally have ordinary people's interests at heart. | Institutional trust |
| C1_03 | The world is becoming a more dangerous place. | Threat perception |
| C1_04 | The way things are going, my children's generation will have a worse life than mine. | Threat perception / decline |
| C1_05 | New ideas and ways of doing things are usually better than the old ones. | Openness to change |
| C1_06 | It is important to protect traditions and ways of life that have served us well. | Tradition |
| C1_07 | Society works best when people respect authority and follow the rules. | Authority |
| C1_08 | People should be free to live as they choose, as long as they do not harm others. | Autonomy |
| C1_09 | The gap between the richest and everyone else is one of the biggest problems facing the country. | Fairness / equality |
| C1_10 | People who work hard generally get what they deserve. | Meritocracy |
| C1_11 | Ordinary people like me have little say in what the government does. | Political efficacy |
| C1_12 | When I set my mind to something, I usually manage to make it happen. | Personal agency |
| C1_13 | Scientific experts usually know better than the general public what is good for society. | Deference to expertise |
| C1_14 | Big technology companies have too much power over our lives. | Corporate power |
| C1_15 | Technological progress has done more good than harm over the past fifty years. | Tech optimism |
| C1_16 | I feel a strong sense of belonging to my local community. | Local belonging |
| C1_17 | I am proud to be [UK: British / US: American]. | National identity |
| C1_18 | We have a responsibility to the people who will live long after we are gone. | Long-term orientation |
| C1_19 | Big changes in society usually end up benefiting people like me. | Change benefit / winners and losers |
| C1_20 | I usually feel that I understand what is going on in the news. | Information confidence |

C2. Which of the following are most important to you personally? Select
up to three. [C2]

Security and safety / Freedom and independence / Fairness and equality /
Family and community / Tradition and faith / Achievement and success /
Care for others / Enjoying life / Protecting the natural world /
Knowledge and understanding

C3. In general, would you say you are someone who worries about the
future a lot, a little, or hardly at all? [C3]

- A lot
- A fair amount
- A little
- Hardly at all

Design note: 20 items is the minimum for a stable latent class solution
across the dimensions above. Items are worded so that no dimension is
carried by a single statement, and pairs (C1_05/C1_06, C1_07/C1_08,
C1_09/C1_10) are balanced in direction to limit acquiescence bias.
Pretest for ceiling effects on C1_01 and C1_08. If a licensed battery
replaces this module, keep C2 and C3 as they feed the messaging guidance
directly.

## Module D: relationship with AI

The rest of the survey is about artificial intelligence.

D1. How often do you use AI tools, such as ChatGPT, Claude, Gemini,
Copilot, image generators or AI assistants? [D1]

- Never
- Less than once a month
- A few times a month
- A few times a week
- Daily or almost daily
- Several times a day

D2. Do you use AI tools in your work? [D2] [Ask if employed,
self-employed or student, from J1; otherwise skip]

- Yes, they are a core part of my work
- Yes, sometimes
- No, but my employer or colleagues do
- No
- Not sure

D3. How would you describe your overall attitude towards artificial
intelligence? [D3]

- Very negative
- Somewhat negative
- Neither positive nor negative
- Somewhat positive
- Very positive

D4. How much do you feel you know about AI and how it works? [D4]

- Nothing at all
- A little
- A fair amount
- A great deal

D5. How much have you heard or read about potential harms and risks from
AI? [D5]

- Nothing at all
- A little
- A fair amount
- A great deal

D6. How much have you heard or read about potential benefits from AI?
[D6]

- Nothing at all
- A little
- A fair amount
- A great deal

D7. How much do you agree or disagree with the following statements?
[D7_01 to D7_06]

[Grid. Strongly disagree to Strongly agree, 5 points. Randomise
order.]

| Code | Statement |
|------|-----------|
| D7_01 | The development of AI will benefit society. |
| D7_02 | The development of AI will threaten society. |
| D7_03 | The benefits of AI outweigh its risks. |
| D7_04 | We should slow down the development of AI until we understand its consequences. |
| D7_05 | AI will make my own life better over the next ten years. |
| D7_06 | The people developing AI are careful about its effects on society. |

D8. When you think about AI, which of these comes closest to how you
feel? Select up to two. [D8]

Excited / Curious / Hopeful / Indifferent / Confused / Uneasy /
Worried / Angry / Powerless

Design note: D7_01 to D7_04 are carried over unchanged from the source
instrument so results can be compared. D1, D3 and D5 are also unchanged.
D8 gives a quick affect measure for everyone before the message
exposure; the fuller 0-10 emotion battery in F4 is exposure-specific.

## Module E: concern across AI issues

People have raised a range of possible problems with AI. We would like
to know how concerned you are about each one. Please answer whether or
not you have heard much about it before.

E1. How concerned are you about each of the following? [E1_01 to
E1_10]

[Grid. Scale: Not at all concerned / Slightly concerned / Somewhat
concerned / Very concerned / Extremely concerned / Don't know enough to
say. Randomise order.]

| Code  | Issue as shown | Category (not shown) |
|-------|----------------|------------------------|
| E1_01 | AI taking people's jobs | Present-day, economic |
| E1_02 | Fake videos, images and news made with AI | Present-day, information |
| E1_03 | AI systems treating some groups of people unfairly | Present-day, discrimination |
| E1_04 | AI being used to watch and track people | Present-day, surveillance |
| E1_05 | Children forming relationships with AI chatbots | Present-day, children |
| E1_06 | A small number of companies controlling powerful AI | Structural, power |
| E1_07 | AI being used in weapons and warfare | Security |
| E1_08 | AI being used to help make dangerous weapons, such as bioweapons | Catastrophic misuse |
| E1_09 | AI systems becoming more capable than humans and acting outside our control | Loss of control / extinction-level |
| E1_10 | The energy and water used by AI data centres | Environment |

E2. And which one of these concerns you most? [E2]

[Single choice from the E1 list, plus "None of these".]

E3. For each of the following, when do you think it is likely to become
a serious problem, if ever? [E3_a, E3_b, E3_c]

[Ask for three issues: the respondent's E2 choice, E1_09 (loss of
control) if not already chosen, and one other drawn at random. Scale:
It's already happening / Within 1-5 years / Within 5-20 years / More
than 20 years from now / Never / Don't know.]

E4. Who do you think should be mainly responsible for making sure AI is
developed safely? Select up to two. [E4]

The companies developing AI / National government / International
bodies such as the UN / Independent regulators / Scientists and
researchers / The courts / The public, through campaigning and voting /
Nobody can control it / Don't know

E5. How much do you trust the following to tell the truth about the
risks of AI? [E5_01 to E5_04]

[Grid. Scale: Do not trust at all / Trust a little / Trust somewhat /
Trust a great deal / Don't know.]

| Code | Row |
|------|-----|
| E5_01 | AI companies |
| E5_02 | The [UK: UK government / US: federal government] |
| E5_03 | Independent scientists |
| E5_04 | Campaign groups and charities |

Design note: the E1 list is balanced deliberately: five present-day
harms, two structural or security items, two catastrophic-risk items and
one environmental item, so that neither the present-day-harms nor the
existential-risk perspective can read the instrument as slanted. Wording
is plain and avoids field jargon such as "alignment", "x-risk",
"algorithmic bias". Check every label against the Common Signals
glossary before fielding.

## Module F: message test

Next, you will read a short text about AI. Please read it closely, as we
will ask you a few questions about it afterwards.

Programming note: randomise each respondent with equal probability to
one condition. Record condition as [F0]. Show the text on its own
screen with a minimum dwell time of 20 seconds before the Next button
appears. Record time on screen as [F0_time].

| Condition | Message type | Specification |
|-----------|---------------|----------------|
| F0 = 0 | Control | Neutral passage of similar length (about 120 words) on an unrelated topic, for example the history of the postal service. No mention of AI. |
| F0 = 1 | Present-day harms, personal frame | A specific current harm (for example, AI-generated scam calls or deepfakes) told through one affected person, ending with a concrete ask. |
| F0 = 2 | Present-day harms, systemic frame | The same harm area framed as a failure of company accountability and regulation. |
| F0 = 3 | Longer-term risk, expert frame | Loss-of-control risk presented via named scientists' warnings and the scale of investment, in measured language. |
| F0 = 4 | Longer-term risk, plain-speaking frame | The same risk in everyday language with no credentials, using the "we are building something we don't understand" framing. |
| F0 = 5 | Benefit-led with conditions | Leads with a concrete benefit (medical diagnosis, for example) then argues safety rules are what make the benefits arrive. |
| F0 = 6 | Bridging | Explicitly links a present-day harm and a longer-term risk as the same problem: powerful systems released faster than anyone can check them. |

Design note: seven conditions at n = 2,000 gives roughly 285 per
condition overall and around 40 to 60 per condition per segment, enough
to detect segment-by-message differences of moderate size but not small
ones. The pilot wave should field a subset of four conditions (0, 1, 3,
6). Messages are written to identical length (110 to 130 words), the
same reading level (target grade 8) and the same structure: situation,
why it matters, what should happen. Every message is drafted with input
from at least one communicator on each side of the field and checked by
both before pre-registration. Final message texts, sources and
readability scores go in Appendix 1 and in the published codebook.
Messages are attributed to no organisation on screen; attribution is
tested separately in Module G.

### F1. Comprehension check

F1. Which of these best describes what the text you just read was about?
[F1]

[Six options, one correct per condition, the same six shown to
everyone. Respondents who fail are retained in the dataset and flagged;
the analysis plan pre-specifies the primary analysis on passers.]

### F2. Reaction to the text

F2. Thinking about the text you just read, how much do you agree or
disagree with the following? [F2_01 to F2_06]

[Grid, Strongly disagree to Strongly agree. Not asked in control
condition.]

| Code | Statement |
|------|-----------|
| F2_01 | It was easy to understand. |
| F2_02 | It was believable. |
| F2_03 | It told me something I did not already know. |
| F2_04 | It felt relevant to my own life. |
| F2_05 | It was trying to frighten me. |
| F2_06 | It made me want to find out more. |

F3. Who do you think wrote this text? [F3]

- An AI company
- A campaign group or charity
- A journalist
- A scientist or academic
- A government body
- A political party
- Someone else
- Don't know

### F4. Emotional response

F4. When you read the text, how much did you feel each of the following,
on a scale from 0 (not at all) to 10 (very strongly)? [F4_01 to F4_06]

[Sliders 0-10. Randomise order. Asked in all conditions including
control.]

Anxious or fearful / Angry / Energised / Hopeless or powerless /
Hopeful / Sympathetic to those affected

### F5. Post-exposure outcomes

Programming note: F5 to F8 are the primary outcome measures and are
asked in every condition, including control, in the same order.

F5. How concerned are you about AI overall? [F5]

- Not at all concerned
- Slightly concerned
- Somewhat concerned
- Very concerned
- Extremely concerned

F6. How much do you support or oppose [UK: the UK government / US: the
federal government] introducing stronger rules on how AI is developed
and used? [F6]

- Strongly oppose
- Oppose
- Neither oppose nor support
- Support
- Strongly support

F7. Would you support or oppose each of the following? [F7_01 to
F7_06]

[Grid, Strongly oppose to Strongly support, plus Don't know. Randomise
order.]

| Code | Statement |
|------|-----------|
| F7_01 | Requiring AI companies to test their most powerful systems for safety before release, with results checked by an independent body |
| F7_02 | Making it a criminal offence to create sexual or violent deepfakes of real people |
| F7_03 | Banning AI chatbots designed as companions for children under 16 |
| F7_04 | Requiring companies to tell you when you are dealing with an AI rather than a person |
| F7_05 | An international agreement limiting the development of the most powerful AI systems |
| F7_06 | Giving workers a legal right to be consulted before AI is used to replace or monitor them |

F8. How willing would you be to do each of the following about AI in the
next 12 months? [F8_01 to F8_06]

[Grid. Scale: Not at all willing / Mostly unwilling / Undecided /
Willing / Very willing.]

| Code | Statement |
|------|-----------|
| F8_01 | Share information about it on social media |
| F8_02 | Sign a petition |
| F8_03 | Contact your [UK: MP / US: member of Congress] |
| F8_04 | Donate to an organisation working on it |
| F8_05 | Talk to friends or family about it |
| F8_06 | Change how you use AI tools yourself |

F9. If a political party made addressing the risks of AI one of its main
priorities, would that change how likely you would be to vote for them?
[F9]

- Much less likely
- Somewhat less likely
- Would not affect my decision
- Somewhat more likely
- Much more likely

### F10. Behavioural measure (optional module)

Below is a link to an open letter calling for independent safety testing
of powerful AI systems before they are released. If you would like to
add your name, click the link, which opens in a new tab, then return
here to finish the survey. Please finish the survey first so that your
answers are saved.

[Link. Record click as F10_click. Do not record whether a signature was
completed. Tell respondents nothing further about the letter until the
debrief.]

Design note: F10 is the one genuinely behavioural outcome in the
instrument and was the strongest feature of the source study. Keep it if
a neutral, real open letter exists that both perspectives in the field
would accept; otherwise drop it rather than fabricate one. The letter
must not be hosted by or attributed to Common Signals.

## Module G: messengers and trust

G1. How much would you trust each of the following to give you accurate
information about AI? [G1_01 to G1_16]

[Grid. Scale: Do not trust at all / Trust a little / Trust somewhat /
Trust a great deal / Don't know. Randomise order. Two screens of
eight.]

| Code | Row |
|------|-----|
| G1_01 | AI researchers and academics |
| G1_02 | Leaders of AI companies |
| G1_03 | Employees who have left AI companies to raise concerns |
| G1_04 | [UK: The UK government / US: The federal government] |
| G1_05 | Independent regulators |
| G1_06 | National charities and campaign groups |
| G1_07 | Trade unions |
| G1_08 | Journalists and news organisations |
| G1_09 | YouTubers, podcasters and online creators |
| G1_10 | Well-known celebrities |
| G1_11 | Religious leaders |
| G1_12 | Doctors, nurses and teachers |
| G1_13 | People who have been directly harmed by AI |
| G1_14 | Military and security officials |
| G1_15 | Your [UK: MP / US: representatives in Congress] |
| G1_16 | Friends and family |

G2. Have you heard of each of the following? If so, how much do you
trust what they say about AI? [G2_01 to G2_15]

[Grid. First column: Never heard of them / Heard of them. If heard of:
Do not trust at all / Trust a little / Trust somewhat / Trust a great
deal. Country-specific list of 12 to 15 named individuals and
organisations drawn from the Common Signals messenger map, balanced
across present-day-harms, existential-risk and bridging voices, and
across institution, campaign group, journalist and creator. Include two
well-known names as recognition anchors. Final list frozen at
pre-registration and published in the codebook.]

G3. In the past month, where have you seen or heard anything about AI?
Select all that apply. [G3]

TV or radio news / Newspapers or news websites / Social media
(Facebook, Instagram, TikTok, X, etc.) / YouTube / Podcasts /
Conversations with friends, family or colleagues / At work / From AI
tools themselves / Films, TV drama or books / Somewhere else / I have
not seen or heard anything about AI in the past month

G4. Is there anyone, a person or an organisation, whose views on AI you
particularly trust? Please name them if so. [G4]

[Open text, optional.]

Design note: G1 extends the source instrument's "who represents your
views" item into a full trust battery; the source item's response set is
preserved inside G1 so the two can be compared. G2 is where the
messenger map is tested empirically for the first time. G4 is coded post
hoc against the messenger map and is the main route for finding trusted
voices the map has missed.

## Module H: civic action

H1. In the last 12 months, have you done any of the following about any
issue you care about, which might or might not include AI? Select all
that apply. [H1]

- Signed a petition (online or in person)
- Contacted your [UK: MP or local councillor / US: member of Congress
  or another elected official]
- Donated to a charity or campaign
- Attended a protest, rally or demonstration
- Shared political content on social media
- Volunteered for a cause or organisation
- Boycotted a product or company for ethical reasons
- None of these

H2. And have you done any of these specifically about AI in the last 12
months? [H2]

[Same list, shown only for items ticked in H1, plus "None of these".]

## Module I: identity and politics

I1 [UK]. If there were a general election tomorrow, which party would
you vote for? [I1]

Conservative / Labour / Liberal Democrat / Reform UK / Green Party /
Scottish National Party / Plaid Cymru / Other / Don't know / Would not
vote

I1 [US]. Generally speaking, do you usually think of yourself as a
Republican, a Democrat, an independent, or something else? [I1]

- Republican
- Democrat
- Independent
- Something else
- Don't know

[If Independent or Something else: Do you think of yourself as closer
to the Republican Party or the Democratic Party? Republican /
Democratic / Neither] [I1b]

I2 [UK]. In the 2024 general election, did you vote, and if so for
which party? [I2]

Conservative / Labour / Liberal Democrat / Reform UK / Green Party /
SNP / Plaid Cymru / Other / Did not vote / Not eligible / Prefer not to
say

I2 [US]. In the 2024 presidential election, did you vote, and if so
for whom? [I2]

- Donald Trump
- Kamala Harris
- Another candidate
- Did not vote
- Not eligible
- Prefer not to say

I3. In politics, people sometimes talk about left and right. Where would
you place yourself on a scale from 0 (left) to 10 (right)? [I3]

[Slider, plus "Don't know".]

I4. Which of the following best describes your religion, if any? [I4]

- No religion
- Christian
- Muslim
- Hindu
- Jewish
- Sikh
- Buddhist
- Another religion
- Prefer not to say

I5. Apart from weddings, funerals and similar occasions, how often do
you attend religious services? [I5]

- Never
- A few times a year
- Monthly
- Weekly or more

## Module J: remaining demographics

J1. Which of these best describes your current situation? [J1]

Working full-time / Working part-time / Self-employed / Unemployed and
looking for work / Student / Retired / Looking after home or family /
Unable to work / Other

J2 [UK]. Which of the following best describes the occupation of the
main income earner in your household? [J2]

- Higher managerial or professional (e.g. doctor, lawyer, company
  director)
- Intermediate managerial or professional (e.g. teacher, middle manager)
- Supervisory, clerical or junior managerial (e.g. office worker, sales
  representative)
- Skilled manual worker (e.g. plumber, electrician, carpenter)
- Semi-skilled or unskilled manual worker (e.g. shop assistant,
  labourer)
- Casual worker, state pensioner or unemployed

J2 [US]. What was your total household income before taxes last year?
[J2]

- Under $25,000
- $25,000 to $49,999
- $50,000 to $74,999
- $75,000 to $99,999
- $100,000 to $149,999
- $150,000 or more
- Prefer not to say

J3. What is your ethnic group? [J3]

[UK: ONS 2021 census high-level categories: White; Mixed or multiple
ethnic groups; Asian or Asian British; Black, Black British, Caribbean
or African; Other ethnic group; Prefer not to say. US: Hispanic or
Latino origin asked separately, then White; Black or African American;
Asian; American Indian or Alaska Native; Native Hawaiian or Pacific
Islander; Another race; Two or more races; Prefer not to say.]

J4. Are there any children under 18 living in your household? [J4]

- Yes
- No
- Prefer not to say

J5. Does your job, or the job you are training for, involve working with
computers or technology most of the day? [J5]

- Yes
- No
- Not applicable

## Module K: in your own words

K1. In one or two sentences, how do you feel about the way AI is
developing? [K1]

[Open text. Optional but encouraged. Minimum box height five lines.]

K2. If you could ask the people building AI one question, what would it
be? [K2]

[Open text, optional.]

Design note: the open-ended answers are coded with the same
five-dimension scheme Common Signals uses for comment-thread analysis,
with Claude as first coder and a human spot-check on a random 10%,
disclosed in the method section. Verbatims are published in full with no
identifiers, as with the comment studies.

## Module L: debrief and close

Thank you. The text you read earlier was one of several short texts
written for this study, each presenting a different way of talking about
AI. Some respondents read a text unrelated to AI. The texts were written
by the research team and drew on published sources; none was produced by
or for an AI company, campaign group or political party. We are studying
how different ways of explaining AI land with different people, so that
those who talk about AI in public can do it more accurately and more
fairly.

Results will be published free at commonsignals.org. If you have any
questions about the study, contact hello@commonsignals.org.

L1. Before you go, do you have any comments on this survey? [L1]

[Open text, optional.]

[End of survey. Redirect to panel completion URL.]

## Appendix 1: message set

To be completed before pre-registration. For each condition record:
final text, word count, Flesch-Kincaid grade, source for every factual
claim, the communicators consulted from each perspective, and the date
frozen. Messages must not name a real organisation or individual.

| Condition | Text | Words | Grade | Sources |
|-----------|------|-------|-------|---------|
| 0 Control | To be drafted | | | |
| 1 Present-day, personal | To be drafted | | | |
| 2 Present-day, systemic | To be drafted | | | |
| 3 Longer-term, expert | To be drafted | | | |
| 4 Longer-term, plain-speaking | To be drafted | | | |
| 5 Benefit-led with conditions | To be drafted | | | |
| 6 Bridging | To be drafted | | | |

## Appendix 2: named messenger list (G2)

Drawn from the Common Signals messenger map sheet at the point of
pre-registration. Requirements: 12 to 15 per country; at least four from
each of present-day-harms, existential-risk and bridging; at least three
organisations and at least three individual creators or journalists; two
recognition anchors with expected awareness above 50%. Record for each:
name, type, perspective tag, primary channel and the map row ID.

## Appendix 3: what changed from the source instrument

| Source element | Treatment here |
|-----------------|-----------------|
| Introduction, consent, Prolific ID | Kept, reworded for a panel rather than Prolific and for open data publication (A0 to A2) |
| AI use, attitude, heard about harms | Kept verbatim (D1, D3, D5); benefit and knowledge items added (D4, D6) |
| Who represents your views (select 3) | Expanded into the messenger trust battery (G1); original categories preserved as rows |
| Civic action in last 12 months | Kept (H1); AI-specific follow-up added (H2) |
| Vignette and treatment/control design | Replaced with a seven-condition message test balanced across perspectives (F); control retained |
| Four agree/disagree statements | Kept verbatim (D7_01 to D7_04), moved before exposure as baseline |
| Regulation support, boycott, voting | Regulation and voting kept as post-exposure outcomes (F6, F9); boycott folded into F8_06 |
| Risk-area-specific concern and willingness blocks | Replaced with a ten-issue concern grid asked of everyone (E1), so concern is measured across the whole risk landscape rather than three areas |
| Comprehension check | Kept (F1) |
| Petition behavioural measure | Kept as optional module with conditions (F10) |
| Emotion, relevance, timing measures | Emotions kept and extended with "hopeful" (F4); relevance folded into F2_04; timing kept for three issues (E3) |
| Demographics | Kept and extended; US variants added; split across B, I and J |
| Open-ended | Kept (K1); second prompt added (K2) |
| Not in source | Values battery for segmentation (C); named messenger grid (G2); media sources (G3); policy items (F7); debrief (L) |

## Open questions for review

Whether to license the More in Common battery or field the original one
in Module C, and on what timeline. Whether the pilot wave fields four or
seven message conditions. Whether a suitable real open letter exists for
F10. Whether E1_09 wording ("acting outside our control") is acceptable
to both perspectives or reads as leading to either. Which fieldwork
partner, and whether they can support the minimum dwell time and slider
items. Ethics review route for an unincorporated organisation.
