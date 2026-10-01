---
title: "Homer skills"
lang: en
---

# Homer skills

A skill is a folder of instructions, reference notes and scripts that Claude
reads before doing a particular kind of Homer work. They live in
`.claude\skills`, the one place Claude Code looks for a project's skills when
it works in this folder, each in its own folder:

- **SKILL.md** at the top: its name, a description Claude uses to decide when
  the skill applies, and the steps.
- **references** (when there is one): notes to read before acting -- rules,
  formats, and the mistakes that have cost a run.
- **scripts** (when there is one): the working scripts, each with a .cmd
  wrapper.

`build` also packs each skill into `exec\skills\<name>.zip`, the form in
which claude.ai takes a skill. How a Homer skill is written is set out in
HomerDev.md, under "Claude skills".

## Skills for Homer collections

- **app-help-guide**: build a help guide for a product from the publisher's
  own help pages -- probe the site, write a fenced harvester, gather the pages,
  build the guide, and run the gates. Also cleans existing guides and decides
  when a site should be refused.
- **blind-creators**: keep the Blind Authors, Blind Developers and Blind
  Presenters directories and the combined Blind Creators listing: vet a person,
  add or update an entry, regenerate the combined list, and audit a file.
- **podcast-directory**: build a one-page directory of a podcast from its RSS
  feed, every episode with date, length, summary and a link that plays it.

## Skills for Homer development

- **homer-build-release**: run and troubleshoot the build, check, tidy, push
  and release cycle, and read the logs those steps leave. Its
  summarizeLogs script turns an uploaded zip of logs into one report: each
  app's build result, check counts, and release outcome.
- **homer-code**: write and review Homer code in Camel Type, in C#, Python,
  JavaScript, VBScript or JAWS script, on the kit's shared classes and
  modules. Carries the kit's style guides, copied from help at each build.
- **homer-convert**: convert files the Homer way -- Markdown to .htm with
  Pandoc, Office, PDF and other documents to accessible .htm or .txt with 2htm,
  tables with inixVert -- and put the output in the Homer encoding with its
  toHomerEncoding script.
- **homer-docs**: the documentation set, reading level, headings, lists,
  links, key naming, History and Hotkeys, with a checkDocs script that reports
  missing documents, stale .htm files, heading problems, bare URLs and each
  document's reading grade.
- **homer-elevate**: the Elevate Version feature -- F11 checks GitHub for a
  newer release and offers its installer -- on an MDI app's Help menu or in a
  single-dialog app's Help box.
- **homer-installer**: the Inno Setup installer -- machine-wide installs, which
  components to offer, the finish page's wording, defaults and order, the
  Results box, and component logging. Carries FinishPage.md from help.
- **homer-migrate**: bring an existing app onto the kit, or audit one that
  has drifted, one app at a time, with a checklist of every area and what each
  looked like when it was wrong.
- **homer-new-app**: start a new app -- choose its shape and language, run
  newHomerApp, fill in the starters, and take it through its first build,
  repository and release.
- **homer-screen-reader**: JAWS scripts and NVDA add-ons -- the same commands
  and keys on both readers, where the files live, how they ship and install,
  compiling for each JAWS version, and diagnosing scripts that do not load.
- **homer-tutorial**: write, check and build the spoken walkthroughs of a
  Homer app, where a narrator works and a screen reader answers. Carries the
  kit's tutorial guide, Tutorials.md, from help.
- **homer-ui**: the interface for screen reader users -- Lbc dialogs and
  focus order, labels and accessible names, access and trigger letters, flat
  menus, hotkeys and key names, the function-key families, and what to speak.
  Carries the kit's own chapters on Lbc, keys, speech and the shapes of app,
  taken from HomerDev.md at each build.

Two documents in the kit's help folder look beyond these skills:
Accessibility Skills for AI Agents (help\A11ySkills.htm) gathers 175 published
accessibility skills from eight collections as a reference, and Homer Skills
(help\HomerSkills.htm) reads them for what they teach the kit and proposes new
and improved Homer skills.
