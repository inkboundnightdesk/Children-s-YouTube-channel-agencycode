# FTC Kids' Privacy Rules — Applied to This Channel

> **Document type: RESTATEMENT.** This is the agency's reading of the law, written by the agency.
> The controlling text is verbatim in [`source_text/coppa-statute-15-usc-6501-6506.txt`](source_text/coppa-statute-15-usc-6501-6506.txt)
> and [`source_text/coppa-rule-16-cfr-part-312.txt`](source_text/coppa-rule-16-cfr-part-312.txt).
> Where this document and the source text disagree, **the source text wins.**
> Official guidance: <https://www.ftc.gov/business-guidance/privacy-security/childrens-privacy>
> Last reviewed: 2026-09-03 · Next review: 2026-12-02

---

## Why COPPA reaches a YouTube channel at all

COPPA regulates "operators" of websites and online services directed to children under 13
(15 U.S.C. § 6501(2); 16 C.F.R. § 312.2). A YouTube channel is not itself the operator of a website —
**Google is.** That distinction matters, and it is the single most misunderstood point in this space.

What it means in practice:

- **YouTube carries the operator obligations** (notice, verifiable parental consent, deletion rights) for
  the platform. That is why the "Made for Kids" setting exists at all: it is how YouTube learns which
  content it must stop collecting data on.
- **You carry the obligation to classify your content truthfully.** Mislabeling child-directed content as
  not-for-kids is what draws FTC and YouTube enforcement. The 2019 YouTube/Google consent order
  ($170M, FTC and NY AG) was built on exactly this failure.
- **The moment you collect anything yourself, off-platform, you become an operator too.** A newsletter, a
  Discord, a contest entry form, a "send us your drawings" address, a fan-mail PO box tied to an email
  list — any of these can make *you* the regulated party, with the full notice-and-consent machinery
  attached. This is why non-negotiable **NN-6** is absolute and why `rules.json` bans the phrases that
  would invite it.

**The channel's position: we are a content supplier to a regulated platform, and we never collect
anything ourselves.** That posture is what keeps the compliance surface small enough to actually hold.

---

## The FTC's six-step compliance plan, mapped

The FTC publishes a six-step plan for COPPA compliance. Here is each step and what it means here.

### 1. Determine whether you are covered

The test in 16 C.F.R. § 312.2 ("website or online service directed to children") weighs subject matter,
visual content, use of animated characters or child-oriented activities, music, age of models, presence of
child celebrities, language, and advertising directed to children.

**Result for us: unambiguously child-directed.** Nursery rhymes, animation, and a preschool audience.
There is no judgment call to make and no argument to have. Every video is Made for Kids.

The 2025 amendments added a **"mixed audience"** category — a service directed to children that does not
target children as its *primary* audience. **We do not qualify and must not try to.** Children are our
primary audience by design.

### 2. Post a clear and comprehensive privacy policy

We do not operate a covered site, so we do not owe a COPPA privacy policy. **But** if the channel ever
gains a website, app, or store, this step activates immediately, and § 312.4 governs what the notice must
say. Treat any proposal for an off-platform property as a **FLAG → escalate to counsel** event.

### 3. Give direct notice to parents before collecting information

Not applicable while NN-6 holds. It becomes applicable the instant anyone proposes a mailing list.

### 4. Get verifiable parental consent

Same. § 312.5 lists the acceptable methods. The 2025 amendments require a **separate** verifiable consent
before disclosing a child's personal information to third parties for targeted advertising — consent to
collect is no longer consent to share.

### 5. Honor parents' ongoing rights

§ 312.6 gives parents the right to review, refuse further collection, and demand deletion. Not applicable
while NN-6 holds.

### 6. Implement reasonable security — and now, retention limits

The 2025 amendments (§ 312.8, § 312.10) go furthest here:

- A **written children's personal information security program**, sized to the sensitivity of the data.
- **Written assurances** from any third party before sharing children's data, confirming they can protect it.
- A **publicly posted data retention policy** stating what is retained, why, and the deletion timetable.
- **Indefinite retention is prohibited.** Data may not be kept "just in case."

**What this means for us even with NN-6 in force:** we hold production data — scripts, renders, sign-off
records, the audit log. None of it is children's personal information, and it must stay that way. Nothing
identifying a child (a fan photo, a name in a message, a child's voice recording) is ever accepted into
this repository. If someone sends one, it is deleted, and the deletion is logged in `audit/decision_log.csv`.

---

## The 2025 amendments — the short list of what changed

Effective June 23, 2025; full compliance required **April 22, 2026** (90 FR 16977).

| Change | Where | Why it matters here |
|---|---|---|
| "Personal information" expanded to include biometric identifiers and government-issued identifiers | § 312.2 | Broadens what an off-platform slip could capture. A child's face or voice in a submitted video is now squarely in scope. |
| New "mixed audience" category defined | § 312.2 | A category we deliberately do not use. |
| Separate consent required for third-party disclosure / targeted advertising | § 312.5 | Reinforces that we never enable personalized ads (NN-2). |
| Written security program mandated | § 312.8 | Applies if we ever collect. Shapes vendor selection now. |
| Written, posted retention policy; indefinite retention banned | § 312.10 | Drives our own "don't accept it in the first place" posture. |
| Safe harbor programs must publicly report members | § 312.11 | Relevant only if we join one. |

---

## Enforcement, plainly

- **The FTC** enforces COPPA violations as unfair or deceptive practices under the FTC Act (§ 312.9;
  15 U.S.C. § 6502(c)). Civil penalties are assessed **per violation** and are inflation-adjusted annually —
  do not rely on any dollar figure you remember; check the current adjusted maximum.
- **State attorneys general** may also bring actions (15 U.S.C. § 6504).
- **YouTube** enforces independently of the government, through its own terms: mislabeled content can be
  removed, monetization pulled, and channels terminated. YouTube's enforcement is faster than the FTC's and
  is the one you will actually meet first.

---

## The one-line version

**Label everything Made for Kids. Never collect anything from anyone off-platform. When in doubt, FLAG it
and ask a lawyer — never guess.**
