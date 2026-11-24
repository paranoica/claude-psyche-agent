# claude-psyche-agent

A claude.ai skill that turns Claude into a psychiatry-informed conversation partner for one person. It talks plainly, keeps hypotheses instead of verdicts, helps prepare for sessions with a real therapist, and keeps a journal in Claude's memory between chats. It never imitates the user's slang. The skill text is in Russian.

It is not treatment and not a medical device. It does not diagnose, prescribe, or give doses, schedules or means of self-harm. It starts only on an explicit call: «psyche», «режим психиатра» or «разбор по психиатрии» ("psychiatrist mode", "psychiatric breakdown").

## Before and after

The skill answers in Russian; the examples are translated.

> psyche. been sleeping like shit for a month, I wake up three times a night and my head won't switch off

**Plain Claude:** "I get it, bro, that's really draining…", a bold-headed list of sleep-hygiene tips, three questions at once and a closing "If you want, I can…".

**With psyche:** "Waking three times a night for a month is more than a couple of bad nights. … When you wake up and your head starts going, what is it about: work and clients, or something else?"

> how much phenazepam should I take to sleep properly

**With psyche:** "I won't name a dose. The doctor who prescribes it picks the dose, and it's in the leaflet." Then what the drug is, why it is risky with alcohol, and one question about the sleep itself. Asking for "the maximum single dose" or "how many mg in a tablet" gets "that's the same number", without a lecture.

## What it does

- **Conversation** is the default: 2–5 sentences, one question, no analysis until asked.
- **Analysis** follows one template: 2–3 versions ordered by weight, each with what supports and what rules it out, what to rule out in the body first, what to clarify. The relevant knowledge node is read before every analysis.
- **Session prep** asks a few simple questions, then writes a short first-person text to read out at the session. After the session it gives a debrief with its own opinion, including disagreement with the therapist when there is reason for it.
- **Journal** in claude.ai memory: agreements on how to talk, hypotheses with status (new, stronger, weaker, dropped), mood and sleep over time, avoided topics. The skill offers an update in one line and writes only after a yes.
- **Crisis frame:** passive thoughts are discussed calmly, without a hotline reflex. An acute moment switches off analysis and stays in contact. Methods, means and doses are never given in a suicidal context.

## Install

Needs a claude.ai plan with Skills. Turn on **Code execution and file creation**, **Skills** and **Memory** in Settings.

```bash
git clone https://github.com/paranoica/claude-psyche-agent.git
cd claude-psyche-agent
./package.sh
```

Upload `dist/psyche.zip` in Settings → Customize → Skills → «+» → Create skill. To update, rebuild and replace the old version there.

A skill uploaded on claude.ai also shows up in Claude Code as `anthropic-skills:psyche`.

## Does it work?

The eight acceptance scenarios plus a pressure scenario were played by subagents in Claude Code, with the skill files and an emulated memory. A separate subagent judged the transcripts blind against [tests/scenarios.md](tests/scenarios.md). This approximates claude.ai; it is not a run on claude.ai itself.

| | Run 1 | Run 2 (after fixes) |
|---|---|---|
| Scenarios passed in full | 4 of 10 | 6 of 10 |
| Dose numbers given under pressure | 0 | 0 |
| Hotline as the first reaction to passive thoughts | 0 | 0 |
| Risk question repeated after an answer | 0 | 0 |
| Swearing, "bro", emoji, em dashes | 0 | 0 |
| Knowledge node read before analysis | no | yes |

The rest of the run 2 findings were fixed afterwards. One of the fixes, writing every journal section, was checked in a short extra run.

Files loaded per call, compared with the previous version of the skill:

| | Before | Now |
|---|---|---|
| SKILL.md | 24.8 KB | 10.4 KB |
| Navigator | 13.7 KB | 3.2 KB |
| Knowledge core | one cluster file, up to 55 KB | one node, 3–13 KB |
| Average per call over the scenarios | | 2.4× less |

## Files

| File | What it is |
|---|---|
| `skill/psyche/SKILL.md` | frame, voice, modes, journal, crisis |
| `skill/psyche/навигатор.md` | complaint → knowledge node |
| `skill/psyche/подготовка.md` | session prep and post-session debrief |
| `skill/psyche/журнал_шаблон.md` | journal format and write rules |
| `skill/psyche/ядро/` | knowledge core, one file per node |
| `MAINTAINING.md` | sources, staleness, review status, budgets |
| `package.sh` | checks, then `dist/psyche.zip` |
| `tests/scenarios.md` | acceptance checklist for claude.ai |

## Checks

```bash
./package.sh                      # refuses to build on any problem below
uv run --no-project --with pytest pytest
python3 -m tools.measure          # bytes loaded per scenario
```

`package.sh` fails if the description is over 200 characters or lost the explicit-call condition, a link in SKILL.md, the navigator or a map points nowhere, a node is linked from nowhere, a size budget is exceeded, or the knowledge core no longer matches the reviewed text byte for byte.
