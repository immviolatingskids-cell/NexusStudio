# Prompt QA: v1.0.1

Primary review target: Gemini at standard density. All fourteen benchmark cases were inspected with their identity anchors, scene inputs, `PromptPlan`, omissions, canonical fallbacks, redundancy notes, conflicts, and final rendered prompt.

## Findings and corrections

The review found compiler issues only. The canonical data, resolver output, scene-mode selection, and pool vocabulary supplied sufficient information for this benchmark; no pool entries were added.

| Benchmarks | Issue | Classification | Change | Result |
| --- | --- | --- | --- | --- |
| Ayami portrait/workplace/lifestyle | Field-like standalone scene clauses; software-work event read mechanically. | COMPILER | Rendered declarative scene clauses and a natural professional event. | PASS |
| Luna portrait/full body/lifestyle | Full-body direction did not explicitly protect feet; lifestyle event was mechanical. | COMPILER | Added entire-figure/feet wording and a deterministic seated everyday event. | PASS |
| Naomi hobby/environmental | Hobby action and pose were adjacent labels; environmental setting lacked priority. | COMPILER | Joined hobby/action wording and moved environmental location ahead of subject action. | PASS |
| Zara portrait | No material prompt issue; reviewed dark hair/build anchors. | — | No change. | PASS |
| Idun portrait/workplace/environmental | Chef activity read as metadata; environmental location needed narrative weight. | COMPILER | Added preparation-counter event and explicit environmental emphasis. | PASS |
| Charlotte portrait/lifestyle | Identity anchors remained clear; lifestyle event had field-like prose. | COMPILER | Used the shared natural event grammar. | PASS |

## Approved benchmark set

Ayami: portrait, workplace, lifestyle. Luna: portrait, full body, lifestyle. Naomi: hobby, environmental. Zara: portrait. Idun: portrait, workplace, environmental. Charlotte: portrait, lifestyle.

The regression suite protects each benchmark’s successful compilation, all six semantic identity-anchor sets, natural activity/pose construction, full-body framing, environmental ordering, and cross-adapter plan parity. Existing v1.0 benchmark hashes remain the approved wording-stability fixtures; the v1.0.1 QA tests add the full fourteen-case Gemini set.

## Remaining limits

Wardrobe remains intentionally broad because the supported vocabulary is broad. Environmental location is still derived only from canonical home and scene defaults, so it establishes place rather than specific architecture or props. Both are intentional scope limits, not prompt compiler defects.
