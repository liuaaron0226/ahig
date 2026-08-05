# /debate

Run a low-token debate loop between Claude and Codex to pressure-test a change without letting the review process become a token sink.

## Goal
- Find real bugs, regressions, and missing edge cases.
- Keep the exchange short and structured.
- Escalate to a larger model only when the cheap pass found a credible issue.

## Core Rules
- Prefer one focused problem at a time.
- Do not paste full files unless absolutely necessary.
- Share only the minimal diff, contract, or failing behavior.
- Limit the loop to 2-3 rounds by default.
- Stop once the same objections repeat or no new evidence appears.
- Use a cheap model for the first pass and reserve the expensive model for final arbitration.

## Recommended Model Split
- Round 1 review: `gpt-5.4-mini`
- Round 2 rebuttal or repair: `gpt-5.4-mini`
- Final sanity check: `gpt-5.5`

If the change is high risk, promote Round 1 to `gpt-5.4` or `gpt-5.5`.
If the change is small and mechanical, keep all non-final rounds on `gpt-5.4-mini`.

## Input Budget
Keep the shared context under 400-800 lines total across all rounds when possible.
- Include only the touched diff and the most relevant surrounding code.
- Summarize constraints instead of re-sending long source files.
- Replace repeated context with a short state summary:
  - what changed
  - what is disputed
  - what was already rejected
