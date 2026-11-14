# Getting started

This page assumes you have never used a terminal or a coding agent. If you have, skip to "Already use Claude Code?" at the end.

## What you need

- **A computer** with macOS or Windows (Linux works too).
- **The Claude desktop app with a paid Claude plan.** The engine runs inside the app's **Code** tab. Anthropic's documentation (checked 13 Nov 2026) says the Code tab needs a Pro, Max, Ultra, Team or Enterprise plan; the free plan does not include it. Plans change, so check [claude.com/pricing](https://claude.com/pricing) before you pay. On Pro, a full session may run past one usage window; you can resume after the reset (see "Stopping and coming back").
- **Python 3.9 or newer.** The engine's small scripts need it: sealing (recording the time and a fingerprint of what you wrote, so any later change shows), reference checks and the dashboard. The agent checks at the start and tells you if it is missing.
  - Mac: the first time a script runs, macOS may offer to install "command line developer tools". Say yes and wait a few minutes.
  - Windows: install Python from [python.org](https://www.python.org/downloads/). If the installer shows "Add python.exe to PATH", tick it.
- **Time.** Plan one to two hours for one question, in several short stops. Simulated sessions took from about 70 minutes to just under two hours; no real user has been timed yet.

You don't need a second AI service or any API key.

## 1 · Get the files

On the [repository page](https://github.com/MichaLie/Research-Intelligence-Engine), click the green **Code** button, then **Download ZIP**. Unzip it somewhere you will find again, such as Documents. You get a folder called `Research-Intelligence-Engine-main`. That folder is the engine: Claude follows the engine's rules only when this is the folder you open in the next step.

If you use git: `git clone https://github.com/MichaLie/Research-Intelligence-Engine`.

## 2 · Open the folder in Claude

1. Install the [Claude desktop app](https://claude.com/download) and sign in.
2. Click the **Code** tab at the top of the sidebar.
3. Under the message box, choose **Local**, then the folder control, **Open folder…**, and pick the engine folder.
4. If the app asks whether to trust this folder, say yes. The folder holds only text files and small Python scripts you can read, and the engine's settings take effect only after you trust it.

## Approval prompts

Before the agent runs a command or changes a file, the app may ask you to approve it. This is normal.

- The engine's own scripts (commands that start with `python3 scripts/`, `python scripts/` or `py -3 scripts/`), the check that Python is installed, and changes inside `sessions/` and `learning/` are pre-approved in `.claude/settings.json` once you trust the folder. If the app asks about them anyway, approve; "always allow" is fine.
- The Librarians may ask to open web pages of open-access papers, and the agent may ask to open the dashboard in your browser. Both are expected.
- Say no to anything that touches files outside the engine folder. If you are unsure what a request is for, ask the agent.

## What leaves your computer

The engine collects nothing. Your question, your hypotheses, everything else you type and the papers you open go to your AI provider (Anthropic, in the Claude app) like any chat, so check your plan's data settings and your institution's AI policy. Searches and reference checks go to PubMed, Europe PMC, OpenAlex, Crossref, DataCite and doi.org, and the Librarians may open open-access papers on publishers' sites. Don't paste unpublished data, or anything your institution does not allow in a cloud AI tool.

## Before you start, have ready

- Your question, in one sentence.
- What you expect the literature to show.
- Two or three hypotheses, and for each, what finding would change your mind.
- The papers you already know, with DOI or PMID if you have them.
- What the answer is for: a paper, a grant, an experiment, a team decision, a thesis chapter.
- The methods, guidelines or tools you plan to use.
- Optionally, who will check your work at the end.

## 3 · Start

Type this and press Enter:

```
Hi, I'd like to start a new investigation.
```

You can write in your own language; searches run in English. The agent (the engine calls it "the colleague") explains the session, asks who will check your work at the end (optional), and then asks six short questions. You answer in the chat and it saves your words exactly as you typed them. Enter sends a message, so for a longer answer, write it in any text editor first and paste it in.

Each message that needs something from you ends with a line starting **Your turn:**.

## The dashboard

After each step the engine rebuilds a page, `dashboard.html`, inside your session folder (`sessions/<date>-<name>/`). The agent gives you its full path the first time and can open it for you. It shows what is waiting on you, anything that needs a look (in red or amber), and which files you wrote and which the agents wrote. It does not refresh itself: reload it in your browser after each step.

## Stopping and coming back

You can stop at any point and close the window. Everything is saved in `sessions/`. Next time, open the same folder in the Code tab and say "hello" or "resume my session"; the agent reads `status.md` in your session folder and goes on from there.

A session uses a lot of agent work. On smaller plans you may hit your usage limit partway through and the agent will stop. Nothing is lost: when the limit resets, open the folder and resume.

## If a search fails

The searches use free public services and need no account. One of them, OpenAlex, gives everyone on the same network a small shared daily allowance, so on a university network its searches can run out. The agent then tells you that the search failed. PubMed and Europe PMC have their own limits and keep working. Try again the next day, or from another network.

## Updating

To move to a newer version, download it and copy your `sessions/` and `learning/` folders into the new folder. Your learning log lives in `learning/LOG.md`.

## Already use Claude Code?

- **Claude Code in a terminal:** run `claude` in the engine folder. The same settings file applies once you trust the folder.
- **Other coding agents:** the instructions are in `AGENTS.md`, a file many coding agents read. None has been tried with this engine. The scripts need internet access, which some agents switch off by default.
- **Any tool without subagents:** the agent will ask you to open a second chat in the same folder for each specialist role and paste one line it gives you.
