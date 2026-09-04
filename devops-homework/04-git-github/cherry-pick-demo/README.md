# `cherry-pick-demo` — branching and `git cherry-pick`

The throwaway repository used to demonstrate cherry-picking in [`../02-branching-and-cherry-pick.md`](../02-branching-and-cherry-pick.md). It follows the assignment exactly: **3 commits on `main`**, then a new branch with **3 commits**, then **one** of those commits cherry-picked back into `main` and verified.

## What the history looks like

```
* 74144c5 (feature/login) Add login tests
* 215b34f Add login validation          <-- the commit that was cherry-picked
* 00d5d73 Add login feature
| * 508ee57 (main) Add login validation <-- the copy, with a DIFFERENT hash
|/
* 3b03c51 Add example config
* ea584c7 Add app entry point
* 5b91527 Initial commit on main
```

`main` ends up with 4 commits, `feature/login` has 3 of its own, and only **one** of those three crossed over. `main` never received `Add login feature` or `Add login tests` — that selectivity is the whole point of `cherry-pick` versus a merge.

| File | What it is |
|---|---|
| [`cherry-pick-demo-output.txt`](./cherry-pick-demo-output.txt) | Full transcript of the demo as it actually ran — every command and its real output |
| `history.bundle` | The repository's complete history (both branches, all 7 commits) as a git bundle |
| [`app.js`](./app.js), [`.env.example`](./.env.example) | Files from the three `main` commits |
| [`validate.js`](./validate.js) | The file the cherry-picked commit brought over |

## Restore the history and check it yourself

```bash
git clone history.bundle cherry-pick-demo-restored
cd cherry-pick-demo-restored
git log --all --graph --oneline --decorate
```

`git clone` from a bundle restores both branches, so you can confirm the two `Add login validation` commits have different SHAs on `main` and `feature/login`.

*(The demo repo's own `README.md` — a one-line `# Demo app` from its first commit — is inside the bundle rather than sitting in this folder, so it doesn't collide with this documentation file. `git log --stat 5b91527` in the restored clone shows it.)*
