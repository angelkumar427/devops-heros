# Multi-branch commits + `cherry-pick`

## The exercise

Exactly as the assignment specifies:

1. Create 2–4 commits on the `main` branch. → **3 commits** were made.
2. Use `git log` to view them.
3. Create a new branch (`feature/login`).
4. Make 2–3 commits on the new branch. → **3 commits** were made.
5. Use `git log` to identify a specific commit.
6. Cherry-pick that one commit from the new branch into `main`.
7. Verify the selected change is now available on `main`.

## Why this is a real workflow, not just a trick

This is the standard move when a feature branch has a fix or piece of work that's ready to ship, but the rest of the branch is still in progress — e.g. a hotfix that happened to be committed on a feature branch, or backporting one commit to a release branch. `cherry-pick` takes the *diff* introduced by a specific commit and replays it on top of your current branch as a brand-new commit (new SHA, same content/message by default).

## Commands used

```bash
git checkout -b feature/login        # branch off main
# ... make commits on feature/login ...

git checkout main                     # back to main
git log --oneline feature/login        # find the SHA of the commit you want
git cherry-pick <sha>                   # replay just that commit onto main
git log --oneline main                   # verify it's there, with a NEW sha
```

If the cherry-picked commit's changes overlap with something already changed on the target branch, you get a **merge conflict** just like a regular merge — resolve it (`git status` shows the conflicted files), then `git add <file>` and `git cherry-pick --continue` (or `git cherry-pick --abort` to back out entirely).

## Hands-on demo (actually run)

Full transcript: [`cherry-pick-demo/cherry-pick-demo-output.txt`](./cherry-pick-demo/cherry-pick-demo-output.txt).
The complete history ships as a git bundle — see [`cherry-pick-demo/README.md`](./cherry-pick-demo/README.md) to restore and inspect it.

What happened:

1. **Three commits on `main`**, each adding a file: `README.md` (`Initial commit on main`), `app.js` (`Add app entry point`), `.env.example` (`Add example config`).
2. `git log --oneline` confirmed all three.
3. Branched with `git checkout -b feature/login`.
4. **Three commits on the branch**, each adding a different file: `login.js` (`Add login feature`), `validate.js` (`Add login validation`), `login.test.js` (`Add login tests`).
5. Identified the target commit programmatically rather than by eye:
   ```bash
   TARGET=$(git log --format='%h %s' | grep 'Add login validation' | cut -d' ' -f1)   # -> 215b34f
   git show --stat $TARGET
   ```
6. Switched back to `main` and confirmed with `ls` that `validate.js` was **not** there yet.
7. Ran `git cherry-pick 215b34f`, which reported:
   ```
   [main 508ee57] Add login validation
    1 file changed, 1 insertion(+)
    create mode 100644 validate.js
   ```
8. **Verified:** `main` now has `validate.js` with the right contents, but still does **not** have `login.js` or `login.test.js`.

```
$ git log --all --graph --oneline --decorate
* 74144c5 (feature/login) Add login tests
* 215b34f Add login validation            <- the original
* 00d5d73 Add login feature
| * 508ee57 (HEAD -> main) Add login validation   <- the cherry-picked copy
|/
* 3b03c51 Add example config
* ea584c7 Add app entry point
* 5b91527 Initial commit on main
```

## The key thing I understood

The same change exists on both branches under **two different SHAs**:

```
on main:            508ee57 Add login validation
on feature/login:   215b34f Add login validation
```

Same subject, same diff, different commit. `cherry-pick` doesn't move or share the original commit — it takes the *diff* that commit introduced and replays it as a brand-new commit on the current branch, with a new hash and a new parent. The original stays untouched on the feature branch.

That is also why `main` received **only** that one change: a merge would have brought all three feature commits and their shared ancestry, whereas cherry-pick copies exactly the commits you name. And it's why cherry-picking the same commit twice, or later merging the branch that still holds the original, can produce duplicate-looking commits or conflicts — the two commits are unrelated objects as far as git is concerned.
