# Task 4 — Git/GitHub Exercises

Two tasks: the difference between `git commit -m` and `git commit -a -m`, and branching with `git cherry-pick`. Both were performed in real throwaway git repositories; each one's full history ships as a **git bundle** so it can be restored and inspected.

---

## Task 1 — `git commit -m` vs `git commit -a -m`

Detailed write-up: [`01-commit-syntax-variations.md`](./01-commit-syntax-variations.md) · demo folder: [`commit-demo/`](./commit-demo/) · [raw transcript](./commit-demo/commit-demo-output.txt)

The demo deliberately makes the plain form **fail**, which is the clearest way to show the difference. Starting from a repo with one tracked file:

```
$ echo "line2" >> notes.txt        # modify an ALREADY TRACKED file
$ git status --short
 M notes.txt                        # modified, but NOT staged

$ git commit -m "Add line2"         # plain -m, nothing staged
On branch master
Changes not staged for commit:
        modified:   notes.txt
no changes added to commit (use "git add" and/or "git commit -a")
(exit code: 1)
```

It fails. Now the same change with `-a`:

```
$ git commit -a -m "Add line2"
[master d296577] Add line2
 1 file changed, 1 insertion(+)
```

It succeeds.

| | `git commit -m` | `git commit -a -m` |
|---|---|---|
| What gets committed | **Only what's already staged** in the index | Staged changes **plus** all modified/deleted **tracked** files |
| Needs `git add` first | Yes | Not for tracked files |
| Picks up brand-new untracked files | No | **No** — these always need an explicit `git add` |

**What I understood:** `-m` only sets the commit *message*; it does nothing about staging. `-a` is the part that auto-stages, and it's limited to files git already tracks. That last row is the trap — `-a` feels like "commit everything", but a newly created file is invisible to it, so `git commit -a -m` can silently leave your new file out of the commit.

---

## Task 2 — Branching and `git cherry-pick`

Detailed write-up: [`02-branching-and-cherry-pick.md`](./02-branching-and-cherry-pick.md) · demo folder: [`cherry-pick-demo/`](./cherry-pick-demo/) · [raw transcript](./cherry-pick-demo/cherry-pick-demo-output.txt)

Done exactly as specified: **3 commits on `main`** → new branch → **3 commits on the branch** → `git log` to find one → cherry-pick it across → verify.

The target commit was identified programmatically rather than by eye:

```
$ TARGET=$(git log --format='%h %s' | grep 'Add login validation' | cut -d' ' -f1)
TARGET=215b34f

$ git checkout main
$ ls                    # validate.js is not here yet
README.md  app.js

$ git cherry-pick 215b34f
[main 508ee57] Add login validation
 1 file changed, 1 insertion(+)
 create mode 100644 validate.js
```

Verification — the file arrived, but **only** that file:

```
$ ls                    # validate.js present; login.js and login.test.js are NOT
README.md  app.js  validate.js

$ git log --all --graph --oneline --decorate
* 74144c5 (feature/login) Add login tests
* 215b34f Add login validation                    <- the original
* 00d5d73 Add login feature
| * 508ee57 (HEAD -> main) Add login validation   <- the cherry-picked copy
|/
* 3b03c51 Add example config
* ea584c7 Add app entry point
* 5b91527 Initial commit on main
```

The same change now exists on both branches under **two different SHAs**:

```
on main:            508ee57 Add login validation
on feature/login:   215b34f Add login validation
```

**What I understood:** `cherry-pick` doesn't move or share a commit — it takes the *diff* that commit introduced and replays it as a **brand-new commit** on the current branch, with a new hash and a new parent. The original stays untouched on the feature branch. That's also why `main` received only that one change: a merge would have brought all three feature commits and their shared ancestry, whereas cherry-pick copies exactly what you name. And because the two commits are unrelated objects to git, later merging the branch that still holds the original can produce duplicate-looking commits or conflicts.

**When you'd actually use it:** a hotfix that got committed onto a feature branch and needs to ship now, or backporting one fix to a release branch, without dragging the rest of the unfinished branch along.

---

## Restoring either demo repository

A git repo can't be nested inside another and stay browsable on GitHub, so each demo's complete history is shipped as a bundle instead of a nested `.git`:

```bash
git clone commit-demo/history.bundle commit-demo-restored
cd commit-demo-restored && git log --oneline

git clone cherry-pick-demo/history.bundle cherry-pick-demo-restored
cd cherry-pick-demo-restored && git log --all --graph --oneline --decorate
```

`cherry-pick-demo` restores with both branches, so the two differing SHAs above can be confirmed directly.
