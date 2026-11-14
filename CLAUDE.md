@AGENTS.md

## Claude Code only

- Start each role with the Agent (or Task) tool, `general-purpose` type, passing the role file's full text and the inputs AGENTS.md lists for that step. Wait for it to finish before the next step.
- Permissions: `.claude/settings.json` pre-approves only the Python version check, the engine's scripts (`python3 scripts/…`, and the `python` / `py -3` forms) and edits inside `sessions/` and `learning/`. Everything else asks the researcher; say in one line what each approval is for.
