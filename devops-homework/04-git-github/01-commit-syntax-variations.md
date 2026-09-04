# `git commit` syntax variations & what they actually do

## `git commit -m "<msg>"`

Commits **only what's in the staging area (the index)**. Anything modified but not `git add`-ed is left out. This is the safe, explicit default — you decide exactly what goes into the commit, one `git add` at a time.

## `git commit -a -m "<msg>"`

`-a` automatically stages every file **git already tracks** that has been modified or deleted, before committing. It does *not* pick up brand-new/untracked files — those still need an explicit `git add` first. Convenient for "I edited some files I already know about," dangerous if you have unrelated changes lying around that you didn't mean to commit together.

## Other common variations worth knowing

| Command | What it does |
|---|---|
| `git commit` (no `-m`) | Opens `$EDITOR` for a multi-line commit message |
| `git commit --amend` | Rewrites the *last* commit (message and/or staged changes) instead of creating a new one — never do this on commits already pushed/shared |
| `git commit -am "<msg>"` | Shorthand for `-a -m` combined |
| `git commit --no-verify` | Skips pre-commit/commit-msg hooks |
| `git commit -S -m "<msg>"` | GPG-signs the commit |
| `git commit --allow-empty -m "<msg>"` | Creates a commit with no changes (useful to trigger CI, or as a placeholder) |
| `git commit -m "<msg>" --author="Name <email>"` | Overrides authorship for this commit |

## Hands-on demo (actually run)

Full transcript: [`commit-demo/commit-demo-output.txt`](./commit-demo/commit-demo-output.txt)

Sequence performed:
1. Created & committed `notes.txt` normally with `git add` + `git commit -m`.
2. Modified `notes.txt` again but **did not** `git add` it.
3. Ran `git commit -m "Add line2"` → **failed**: `no changes added to commit`, because nothing was staged.
4. Ran `git commit -a -m "Add line2"` on the exact same working tree → **succeeded**, because `-a` staged the tracked, modified file automatically.

This is the cleanest way to see the difference in practice: same working-tree state, same message, one form fails and the other doesn't — because of what's staged vs. what's just sitting modified in the working directory.
