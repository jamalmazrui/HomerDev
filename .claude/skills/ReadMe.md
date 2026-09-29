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

`buildHomerDev` also packs each skill into `exec\skills\<name>.zip`, the form in
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

- **homer-tutorial**: write, check and build the spoken walkthroughs of a
  Homer app, where a narrator works and a screen reader answers.
