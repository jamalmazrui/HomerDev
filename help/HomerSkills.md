# Homer Skills: What the Accessibility Skills Teach

## Contents

- [Introduction](#introduction)
- [Learnings that fit HomerDev](#learnings-that-fit-homerdev)
- [Questions before adopting](#questions-before-adopting)
- [Proposed new skills](#proposed-new-skills)
- [Proposed improvements to existing skills](#proposed-improvements-to-existing-skills)
- [Suggested order](#suggested-order)
- [Learnings from the skill and agent guides](#learnings-from-the-skill-and-agent-guides)
- [Learnings from Anthropic's skills repository](#learnings-from-anthropics-skills-repository)

## Introduction

This document reads the 175 accessibility skills gathered in [Accessibility Skills for AI Agents](https://github.com/JamalMazrui/A11ySkills), a separate repository that states each skill's license (142 are MIT and 33 are under the GNU Affero General Public License, so the full texts are kept there rather than copied into this MIT-licensed kit), and asks what they teach the Homer Development Kit. It has three parts: learnings that agree with the HomerDev guidelines and can be adopted, questions where a learning would change or stretch a guideline and so needs a decision first, and proposals for new and improved Homer skills.

The skills come from eight collections. Three shapes recur:

- **A team of small skills with a shared contract** (Community Access, 108 skills). Routers pick specialists; specialists return findings in one JSON schema; helpers do mechanical work; reference skills hold rule tables. Only routers can be chosen by the model, so the rest cost nothing until named.
- **Long rule sets, one per pattern** (Mike Gifford, 33 skills). Each opens with when to load it, states its rules firmly, and ends with how to test them, with a Planner and a Critic that weigh evidence rather than check.
- **Short checklists** (Axel, 10 skills; Seth Hobson, Addy Osmani, Magnus Hedemark), and **tool-driven audits** (Agentic QE), which run axe-core, pa11y and Lighthouse and carry their own evaluations.

The 14 Homer skills are a fourth shape: eleven hold the rules for building Windows programs for screen reader users, and three build reference collections in the same style. They are kept short (58 to 167 lines each, well under the standard's 500-line limit), with detail in references, and every one follows the standard's naming and description rules.

## Learnings that fit HomerDev

Each of these agrees with the HomerDev guidelines as they stand; several confirm a Homer rule from another direction.

- **Fix it where it starts.** Mike Gifford's upstream-first skill says to fix a barrier in the shared component or design system it comes from, not in each page. This is the Homer rule that Lbc owns focus order and is fixed in Lbc, not in the app, and the reason for the kit itself.
- **One shared contract, read by every skill.** Community Access's core skill holds the rules every skill follows (tiers, how one skill hands work to another, the findings schema, report rules), so no skill repeats them. HomerDev.md does this for the Homer skills, which take their rules from it at each build.
- **Findings as data, then a report.** Community Access's specialists return only JSON in one schema, with a severity and a confidence for each finding; a script renders the report and keeps each run in a history folder, so a regression detector can compare runs. Homer's check already writes an evidence report; the same findings could also be written as data, so two runs can be compared.
- **Verify the fix.** A verifier re-runs the one test that found a problem after it is fixed. Homer's check runs before every release; a fix to an app could name the finding it closes and re-run that check alone.
- **Test with real assistive technology.** Every collection that mentions automated scanning says it finds a third or so of problems, and that testing with JAWS, NVDA, Narrator and VoiceOver finds the rest. Mike Gifford's Critic adds a caution: an AI must not claim to know a disabled person's experience. Homer's practice of testing with real readers, and taking reports from beta testers, is the same.
- **A simulated listener, clearly labelled.** Community Access's Screen Reader Lab walks HTML in reading order, tab order, heading order and form order, saying what a screen reader would announce, with a disclaimer that real readers differ. The same idea suits Homer dialogs (see homer-listen below).
- **Name, role, value and state for every control.** The desktop specialist's baseline: each control exposes all four through UI Automation, and keyboard use comes first. Its wxPython advice, to put a visible label immediately before its control, is the Homer rule that a preceding label names a control, and its warning that a set name is ignored when it conflicts matches the Homer rule against an accessible name that repeats the caption.
- **Visible words are the spoken words.** The speech recognition skill (voice control with Windows Voice Access or Dragon) needs each control's spoken name to contain its visible label. Homer controls already take their names from their captions and preceding labels.
- **Announce only what the reader cannot know.** The live region skills warn against announcing what assistive technology already says. This is the Homer rule against duplicating the screen reader.
- **Single-key commands only where the focus is.** WCAG 2.1.4 allows a shortcut of one printable character when it works only while its control has focus. Homer's single-key commands, such as Question Mark in FileDir's file list, work only where they belong, so they meet it.
- **Plain language and a measured reading level.** Both Community Access and Mike Gifford measure reading level and treat dense jargon as a barrier. Homer's documentation already has a reading-level rule (see the questions below on the target).
- **Links that say where they go.** The Markdown and link skills flag vague link text, bare addresses and missing alternatives for images and diagrams, as Homer's documentation rules do.
- **Reference skills cost little.** Community Access marks rule tables as reference data, read only when another skill needs them. Homer's references folders do the same.
- **Descriptions that name the request.** Skills that are chosen reliably say when to use them in words a request would contain ("Use when ...", "Load this skill whenever ..."). The Homer skills follow this; a few could add the plain words people use, such as "installer" beside "Inno Setup".
- **Skills tested like code.** Agentic QE ships a schema, a validator and evaluations with each skill, so a change can be shown not to break it.

## Questions before adopting

Each of these would change, extend or loosen a HomerDev guideline, so none is adopted until you decide.

- **Reading level: grade 8 or 9?** Community Access and Mike Gifford use grade 8, after WCAG 3.1.5 (Level AAA), which asks for "lower secondary education". Homer documentation targets grade 9. Keep 9, or move to 8?
- **An Accessibility document for each app?** Mike Gifford's accessibility-general skill centres on an ACCESSIBILITY.md in each project: what the project commits to, known issues, and how to report a barrier. Community Access writes accessibility statements and conformance reports (VPATs). Homer's standard set is ReadMe, the guide, Developer, License, History and Hotkeys. Add Accessibility.md, or a conformance report, to the set?
- **Gender-neutral and inclusive wording.** Mike Gifford's content-design skill lists "gender-neutral and inclusive language throughout" among its style points. Homer tools do not police language. The recommendation is to leave this out of every Homer skill; confirm?
- **Tables for findings.** Most collections report findings in tables. Homer prefers lists, except in reports for usually sighted managers and developers. A findings report under the proposed homer-audit would be such a report; tables there?
- **The NVDA Add-on Store.** Community Access's NVDA specialist covers publishing to NV Access's Add-on Store, with its metadata schema and validation. Homer installs its add-ons directly, from its own installers. Also submit Homer add-ons to the store, or keep to the installers?
- **Narrator and Voice Access in testing.** Several skills test with Narrator and with voice control as well as JAWS and NVDA. Add them to the Homer test pass, or keep to JAWS and NVDA?

## Proposed new skills

Revised in 1.47.0: fewer skills, and measurement first. Each new skill costs
upkeep, and every skill an AI loads takes room in its context, so a proposal
that an existing tool can absorb is folded into that tool instead.

- **Measure before adding (done in 1.47.0, as a script, not a skill).**
  scripts\evalSkills asks Claude Code to write the same small program several
  times without the Homer skills and several times with them, builds each one,
  and scores both sets with check and uiCheck. Without that evidence nobody,
  Homer included, can say that a skill helps; with it, every proposal below
  can be judged by whether the numbers move.
- **homer-listen.** Predicts what JAWS and NVDA will say in a Homer dialog or menu, read from its Lbc source: each control's name, role and state in focus order, with trigger letters and hotkeys. It flags what the Homer rules forbid: a name that repeats its label, two items claiming one trigger letter, a trigger letter in the middle of a word, app speech that repeats what the reader says, and a control with no name. Because a confident prediction can stand in for the real check it was meant to support -- a risk that falls hardest on a blind developer -- every report opens with the word "Prediction" and ends with what still has to be heard in a real screen reader.
- **uiCheck, extended (instead of a new homer-ui-check skill).** uiCheck already starts a program and reads the UI Automation tree a screen reader reads. Extending it to record each control's name, role, value, state, focusability and access key, and to test the Homer rules homer-listen predicts, gives the same proof without another skill to maintain.
- **homer-audit, ending in the test pass.** One entry point for an app's review, as Community Access's Accessibility Lead is for theirs: it runs check, uiCheck and the finish-page and Local-tree checks; writes the findings as data, each with a severity; compares them with the last run, saying what is new, what is fixed and what has regressed; and ends by writing the manual test pass for the release from its History and Hotkeys -- each changed command to try with the keyboard, then JAWS, then NVDA. One skill rather than homer-audit and homer-test-pass, since the second is the last step of the first.
- **homer-bug-report.** Turns logs and a description into a report an app's developer can act on: what was done, what was expected, what happened, the version, Windows and screen reader, and the log lines that matter. It follows Mike Gifford's bug-reporting skill, adapted to the Homer log layout, for beta testers' messages and GitHub issues.

## Proposed improvements to existing skills

Kit 1.50.1 added the parts of these that settle no open question: homer-docs
now flags vague link text and images with no text alternative; homer-ui
gains the spoken-words and one-key-command rules and a UI Automation
reference; homer-screen-reader gains NVDA's script fields and testing in the
reader; homer-code gains fixing at the source and trying changes with the
readers; homer-build-release gains showing that a fix worked. Still open:
emoji and tables in the Markdown check, NVDA manifest validation, evaluation
prompts, and reworded descriptions.

- **homer-docs**: check Markdown the way the Markdown skills do, as a script: vague link text, bare addresses, skipped heading levels, more than one H1, an image or diagram without a text alternative, emoji used as words, and tables where a list would serve. Measure the reading level of each document against the Homer target and report it.
- **homer-ui**: add a short UI Automation reference, with the name, role, value and state each Lbc control exposes and which patterns screen readers use (invoke, value, selection, expand and collapse, toggle), so a new control is checked against it.
- **homer-screen-reader**: add NVDA's script decorator fields (`description`, `gesture`, `category`, `speakOnDemand`) and when `ui.message` is right, from the NVDA specialist; validate the add-on manifest; and repeat that a script is tested in the reader itself.
- **homer-build-release**: name the finding a fix closes, and re-run only that check after it, as the verifier does.
- **homer-code**: ask for a test with real assistive technology in a change's evidence, as the testing skills do, so automated checks are never the whole proof.
- **All Homer skills**: a few evaluation prompts each, with the expected behaviour, checked by the kit's build, as Agentic QE does; and a review of each description for the plain words a request would use.

## Suggested order

- First, run evalSkills and keep its report. It is the baseline every later
  change is measured against.
- Then extend uiCheck, so the running program is tested for the rules that
  matter most to screen reader users.
- Then homer-listen, always labelled as a prediction, checked against uiCheck.
- Then homer-audit, which joins them with the existing checks, compares runs
  and ends with the manual test pass.
- Then the homer-docs Markdown check and homer-bug-report.
- After each step, run evalSkills again: a skill that does not move the numbers
  is a candidate for removal, not a reason for another skill.
- The questions above can be settled at any point; each answer becomes a HomerDev guideline before any skill relies on it.

## Learnings from the skill and agent guides

*Added in kit 1.59.0, from four guides read in October 2026: Anthropic's Complete Guide to Building Skills for Claude (January 2026) and its Building Effective AI Agents, OpenAI's A Practical Guide to Building Agents, and Google's Adaptation of Foundation Models whitepaper.*

The skill guide gives exact rules, and the Homer skills already met most of them: kebab-case folder names, a SKILL.md in each, no README inside a skill folder, a description that says what the skill does and when to use it, and bodies far under the 5,000-word limit. Checking them found one rule broken four times: angle brackets in a description (`<App>` three times, `<singular>` once). The guide warns that the frontmatter goes into the system prompt, so a skill holding an angle bracket is refused at upload. Those four now use the kit's own placeholder, `_APP_`.

What the guides teach, and what the kit now does with it:

- **Check exact rules with a script.** The skill guide's advice is that code is deterministic and reading is not, so a rule that must hold is checked by a program. The kit's new `scripts\checkSkills` checks every skill in a project against the guide's rules and exits 1 on a problem: run it after writing or changing a skill, as checkTutorial is run after writing a walk.
- **The description is how a skill is chosen.** It is always in the model's context; the body is read only when the skill is chosen, and references only when needed. So the description carries the work and the words a request would contain, and detail goes to references. This is the Homer pattern already; checkSkills gives a notice when a description does not say when to use the skill.
- **Test the choosing, not just the result.** The guide's tests are three kinds: prompts that should load the skill, paraphrases that should still load it, and unrelated prompts that should not; then whether the result is right; then whether the skill beats working without it. The kit's evalSkills measures the third. Writing ten prompts that should load each skill and five that should not, and asking "When would you use the homer-db skill?" to hear the description quoted back, would cover the first two.
- **Put critical instructions first, briefly.** When a skill's instructions are not followed, the guide finds them too long, buried or ambiguous. Homer skills open with their rules; keep it so, and move worked detail to references as the homer-tutorial skill grows past 3,000 words.
- **Start with one agent, and keep it simple.** Both agent guides recommend one agent with good tools before several, and splitting only when instructions sprawl or similar tools are confused. This matches the Homer preference not to over-engineer.
- **A person decides what cannot be undone.** OpenAI's guide names two reasons to hand control back to a person: repeated failure, and actions that are irreversible or high-stakes. The Homer rule that a book's manuscript or cover is never sent to KDP without the author's word is this rule; the kit's scripts that publish, release or upload should keep it.
- **One writes, another checks.** The evaluator-optimizer pattern pairs a generator with an evaluator against clear criteria, and is worth its cost only where the criteria are clear. This is the author's practice of having one AI audit another's work, and the Homer checkers are the clear criteria that make it pay.
- **Keep what a tool returns small.** Long tool output crowds out reasoning; the guides advise paging, filtering and truncation with sensible defaults. Homer tools already keep the console short and put detail in the log, which is the same rule for a person.

The foundation-model whitepaper is about tuning and serving models on Google's platform, and holds nothing a Homer skill needs.

Questions before adopting:

- **Trigger tests in each skill?** Should each Homer skill carry a short `references\triggers.md` of prompts that should and should not load it, for evalSkills to run?
- **A version in each skill's metadata?** The guide suggests `metadata: version:` so a changed skill can be told from an old one. The kit's own version could serve, written into each skill by the build.

## Learnings from Anthropic's skills repository

*Added in kit 1.60.0, from Anthropic's public skills repository (anthropics/skills, 17 skills, read 7 October 2026), above all its skill-creator.*

- **The official validator, now in checkSkills.** The skill-creator's own checker, quick_validate.py, allows only six frontmatter keys (name, description, license, allowed-tools, metadata, compatibility; custom values go under metadata), and limits a name to 64 characters with no hyphen at either end and no two together. checkSkills now applies all of it.
- **Calibrated on Anthropic's own skills.** Run over the repository's 17 skills, checkSkills found 2 problems, both real (the claude-api skill uses the reserved word and has a 1,068-character description), and showed that a body past 5,000 words is advice, not a rule: Anthropic's skill-creator runs 5,151 words and the validator does not count words. That check is now a notice, as is a body past the skill-creator's ideal of 500 lines.
- **Test the choosing with near misses.** The skill-creator's description check uses 20 realistic requests, 8 to 10 that should load the skill and 8 to 10 that should not, and the valuable negatives are near misses: requests that share the skill's words but need something else ("Write a fibonacci function" tests nothing for a PDF skill). It runs each request three times and splits them 60 to 40 so a better description is judged on requests it was not tuned on. That answers the question above about trigger tests in each skill: if adopted, each Homer skill's trigger file should hold near misses, such as a C# question that is not a Homer program for homer-code.
- **Explain the why, keep it lean.** Its advice for improving a skill: generalize from feedback rather than patching one case, remove what is not pulling its weight, explain the reason behind each rule rather than shouting it, and when every test run writes the same helper script, put that script in the skill. The Homer skills already explain their reasons; the last point argues for moving repeated checks into scripts, as checkTutorial and checkSkills do.
- **Look before acting on a web page.** The webapp-testing skill's pattern: wait for the page to settle, inspect what is really there, then act on the controls found. The kit's browser scripts for KDP, Author Central and Draft2Digital already work this way (kdpSubmit --inspect records a page's controls); it is the right model for any new one.
- **Close a substantive answer with questions that check it.** The discernment-nudge skill has an assistant end advice, a plan or an estimate with two or three short questions tied to what it just said, to help the reader check the facts and the reasoning. That fits the course on AI-assisted development more than the kit: it is a habit to teach.
