# Research Intelligence Engine

**Your judgment first, then the agents.**  
[Concept page](https://michalie.github.io/Research-Intelligence-Engine/) · [Getting started](SETUP.md) · [Agent Risk Atlas](https://michalie.github.io/agent-risk-atlas/)

AI agents can now search, read and summarise the literature in minutes. The risk is that the agent frames the question, picks the evidence and writes the conclusion, and your own judgment gets less use. The [Agent Risk Atlas](https://michalie.github.io/agent-risk-atlas/) maps 47 ways research with AI agents goes wrong, among them deferring to the agent's framing, reading abstracts only, and fluent reports that outrun their evidence.

This engine reverses the order. You put your own view on record first. Four specialist roles then expand it, search for and against it, attack it and check your argument, and you write the conclusion. It is a set of instructions and small scripts that run inside an AI coding agent.

It is for PhD students and for researchers at any stage. The result is addressed to your second reader, whoever checks your work: a supervisor, a senior researcher, a team expert or a co-author.

## What you get

- Your argument in your own words, each claim checked against its evidence by a separate agent.
- Every cited reference checked for existence and retraction, and every quote taken from a saved full text looked up in that text.
- The agents' own answer, shown after you have written yours.
- A handoff for your second reader, with a list of facts about how AI was used.
- A session dashboard and a private learning log.

## Start

New to coding agents? Follow [SETUP.md](SETUP.md), which uses the Claude desktop app.

Already use Claude Code? Open this folder in it and type `Hi, I'd like to start a new investigation.` You need Python 3.9 or newer and internet access. No API keys. Other coding agents that read `AGENTS.md` may work; none has been tried.

## How a session goes

1. You answer six short questions: your question, expectations, hypotheses, papers, purpose and methods. Scripts seal this brief before any agent output exists (they record the time and a fingerprint of the file, so any later change shows) and check your papers.
2. The Deep Analyst adds hypotheses your brief did not use. You decide what to adopt.
3. Two Librarians search, one for your main hypothesis and one against it, and pick one passage for you to read yourself.
4. You name the weakest point of your case, read the Critic's report and choose how to go on. The colleague (the agent that runs the session) gives its own view only after you choose. Two to five rounds.
5. You settle the threads still open, write your argument, and Fresh eyes checks every claim without suggesting wording.
6. You write two questions for your second reader and compare your argument with the agents' answer.

Plan one to two hours per question: simulated sessions took from about 70 minutes to just under two hours, and no real user has been timed yet. Ask for agents-first mode to see how much the agents' framing shapes your conclusion; that mode has not yet been run as a full session.

## What leaves your machine

The engine collects nothing. What you type and the papers you open go to your AI provider like any chat, and searches and reference checks go to six public literature services. Sessions stay in this folder. Don't paste unpublished data, or anything your institution does not allow in a cloud AI tool. [SETUP.md](SETUP.md#what-leaves-your-computer) has the full list.

## Limits

- One model plays every role, so the agents share its blind spots. If you also use a coding agent from a second AI provider, you can run Fresh eyes there: ask the colleague for the line that starts it. This route has not been tried.
- The rules in `AGENTS.md` are instructions, and an agent can break them. The dashboard shows skipped or out-of-order steps in red or amber.
- It has been tested only in Claude Code, with simulated PhD students; the [concept page](https://michalie.github.io/Research-Intelligence-Engine/#tested) has the results. The newest parts (the list of open threads, the quote check and the start path in SETUP.md) have not yet been used in a full session. No real user has tried it.

## More

- The concept page names the atlas risk each step guards against.
- Version 1 (February 2026) is kept under the git tag v1.0.

## Questions and problems

Open an issue on the [repository page](https://github.com/MichaLie/Research-Intelligence-Engine/issues).

## Author and licence

By Michaela Liegertová, built with AI agents (Claude, by Anthropic). Code: MIT ([LICENSE](LICENSE)). Text: CC BY 4.0 ([LICENSE-content.md](LICENSE-content.md)). To cite it, see [CITATION.cff](CITATION.cff).
