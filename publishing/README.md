# /publishing/ — The Last Mile

| File | Purpose |
|---|---|
| [`youtube_upload_checklist.md`](youtube_upload_checklist.md) | Step-by-step upload, with the MFK verification that catches the expensive mistake |
| [`metadata_template.json`](metadata_template.json) | The metadata contract, with each non-negotiable annotated |
| [`scheduling_rules.md`](scheduling_rules.md) | Volume caps and cadence — NN-3 enforced by the calendar |

## Nothing here is automated, on purpose

This repository does not touch the YouTube API. There is no upload script, no OAuth flow, no `--publish`
flag. **A human uploads, every time.**

That is a deliberate design decision, not an unfinished feature. The maintenance rule says "never
auto-publish without a human passing the review gate," and the only way to guarantee that in software is
to make the software incapable of publishing at all. Automating the last mile would mean the worst
possible failure — a bad video going live unattended — becomes the *easy* failure.

## The flow

```
build/<ref>/publish_package.json   (verdict: PASS)
        |
        v
youtube_upload_checklist.md   <- a human, in YouTube Studio
        |
        v
audit/published_index.json    <- append the row, or duplicate detection goes blind
audit/decision_log.csv        <- log the publish
```

## The single highest-value check on the page

After setting Made for Kids, look at whether comments and notifications are actually off. If they are not,
**the setting did not take.** That one look is worth more than every other item on the checklist combined.
