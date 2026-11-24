# Maintaining psyche

Notes for whoever edits the skill. Nothing here is uploaded to claude.ai.

## What loads when

| file | loaded |
|---|---|
| `SKILL.md` | every call |
| `навигатор.md` | when an answer needs clinical knowledge, and before every analysis |
| `ядро/<folder>/<node>.md` | one node per topic, picked from the navigator |
| `ядро/фарма/_карта.md`, `ядро/методы/_карта.md` | on a question about drugs or therapy methods |
| `ядро/фарма/_рамка.md`, `ядро/методы/_рамка.md` | first time a session enters that block |
| `ядро/антипаттерны/*.md` | under pressure, salami slicing, self-diagnosis |
| `подготовка.md` | therapy-session prep and post-session debrief |
| `журнал_шаблон.md` | before writing to the journal |

`ядро/антипаттерны/_как_пользоваться.md` is linked from nowhere on purpose: its rule ("warm honesty, the frame does not bend under pressure") lives in SKILL.md §8.

## Load budget

The original target was at least 3× fewer bytes per typical call than the previous version of the skill. That version is not in this repository; its file sizes are recorded in `tools/measure.py`.

```
python3 -m tools.measure
```

At the time of writing: 2.5× in total, 2.4× on average over the eight acceptance scenarios, 1.8× in the worst one (session prep). Before the behaviour rules below it was 3.1× on average. They cost about 2.5 KB of SKILL.md and were judged more important than the number. Nodes that were already a file of their own in the old core (sleep, ADHD, eating, psychosis, BPD, substances) are 11–13 KB each and cannot shrink without editing the content.

`tools/check_skill.py` enforces SKILL.md ≤ 10500 bytes and the navigator ≤ 4000 bytes. §7 alone is about 2.5 KB of SKILL.md.

## Section numbers in SKILL.md

Core nodes refer to `SKILL.md §0`, `§3` and `§7`. Keep those numbers when restructuring SKILL.md, or update every reference under `ядро/`.

## Knowledge core

Node formats:
- diagnosis: key signs; differential (what supports / what rules out each version); rule out the body first; what to ask; red flags; source pointer;
- drugs (`фарма/`): class and mechanism; why a doctor may prescribe; course without doses; side effects; dangerous interactions and red flags; drugs by INN with registration status and foreign brands; sources;
- methods (`методы/`): what it is; evidence; how it works in practice; what to expect; red flags; sources.

All blocks, including the antipatterns, were reviewed and approved by a practising physician. Validation means two pairs of eyes (one physician plus the author), not a multi-reviewer process. Keep that in mind for the crisis and pharmacology parts. New content goes into the core only after the physician approves it.

### Split provenance

The first commit holds the reviewed cluster files. `tools/split_core.py` split them into one file per node; node text is byte-identical. Only the file headers (title, review status, format notes) and the `---` separators between nodes were dropped. `./package.sh` re-runs the comparison on every build:

```
python3 -m tools.split_core --rev 9f920c0 --check
```

The first intended content edit makes this check fail. At that point, delete `tools/split_core.py`, its test, and the `split_core` call in `tools/package.py` in one commit, and say why in the message.

### Adding a node

1. Write `ядро/<folder>/<node>.md` in the format of its block.
2. Add a row to `навигатор.md`, or to the block's `_карта.md` for drugs and methods.
3. Add the file to `HANDWRITTEN` in `tools/split_core.py` while the split check still exists.
4. Run `./package.sh`. It fails on broken links and on nodes nothing links to.

## Sources and staleness

- Stable clinical knowledge (how SSRIs work, what CBT is, how criteria are built) is not searched for at runtime. Live search covers only what changes: new drugs, availability, current recommendations, whether a resource still works.
- The core holds the author's own summaries. Open material (public domain, ICD-11 from WHO, open-access papers) may be quoted. Copyrighted material (DSM-5-TR, textbooks, paywalled papers) is only summarised, with a pointer to the original. Each claim has a pointer back to its source.
- Things that go stale:
  - registration flags in `ядро/фарма/` (the national register changes). They are marked preliminary; re-check them against the register when in doubt and roughly every 6–12 months. The register and the physician have the final word;
  - ICD-11 codes and thresholds (WHO revisions) and "first-line" status of methods (APA, NICE, VA/DoD and Cochrane updates). Re-check when classifications or guidelines change;
  - helplines and other resources that shut down.

## Memory journal

The journal is a claude.ai memory file, `areas/psyche.md`. Format and write rules are in `skill/psyche/журнал_шаблон.md`. If the account already has memory files for the profile, health or therapy, the journal links to them instead of copying, and new facts go there. Write the journal in the same language as the rest of the memory.

Memory on claude.ai is written only when the user asks, refuses some categories by its own rules, and runs a consent check for health data. The skill offers an update in one line when the user closes a session or after a therapy debrief, and reports what did not save. The offer line is short; the write itself updates every section of the template.

## Changes from the previous version

- The old style section (lowercase, swearing, imitating the user) is removed. The global output style applies, plus a short voice block in §1.
- Build notes (sources, review) moved here; the core map moved to the navigator.
- File-based profile and notes are gone, replaced by the memory journal.
- New: three response modes in §5, session prep and debrief in `подготовка.md`.
- §7 keeps its content. Em dashes became punctuation, and the antipattern references point to the new files.

## Where the behaviour rules come from

A long log of this kind of conversation with plain Claude was reviewed to see what goes wrong. It is not stored here. What it changed:

- §4: check facts (who said what) before concluding; guesses about motives are questions, not facts; a position changes on new facts, not on pressure, and the change is named; answer every point of a long message; give an own opinion when asked; no stock coping techniques or chores ("go to sleep", "eat"); ask about risk once and accept the answer; no therapist refrain.
- §1: no «брат», emoji or bracket smileys. §3: no regimen advice either, and the refusal is one line.
- Session prep became a short interview, then first-person prose without lists or clinical headings, only the user's own topics.
- The journal got an Agreements section, and the skill says «запомнил» only after a successful write.

Two runs of the acceptance scenarios with subagents playing the skill then added: read the node before any analysis; order versions by weight and, under «скажи уже», name the one that led in the analysis; follow rules silently instead of announcing them; no sympathy openers or option menus; refuse doses by role, not by missing data; separate the short journal offer from the full write.

## claude.ai specifics

- The description is capped at 200 characters and must keep «ТОЛЬКО по явному вызову». `tools/check_skill.py` enforces both.
- A skill uploaded on claude.ai syncs into Claude Code as `anthropic-skills:psyche`. Check after each upload that it does not trigger on its own there and does not collide with a local copy.
- claude.ai account settings leak into `claude -p` runs even with an isolated HOME, so local runs are only approximations. Acceptance runs on real claude.ai, see `tests/scenarios.md`.

## Known gaps

- The pharma block does not cover every drug. Adding a node is content work and needs the physician's review. Until then, the pharma map tells the model to say the drug is missing and explain at the class level.
- Not yet checked on real claude.ai: the memory write (including the consent check for health data) and whether the synced skill stays quiet in Claude Code.
