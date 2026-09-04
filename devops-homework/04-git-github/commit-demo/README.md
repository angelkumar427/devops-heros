# `commit-demo` — `git commit -m` vs `git commit -a -m`

The throwaway repository used to demonstrate the difference between the two commit forms in [`../01-commit-syntax-variations.md`](../01-commit-syntax-variations.md).

| File | What it is |
|---|---|
| [`notes.txt`](./notes.txt) | The one tracked file the demo commits to (`line1`, then `line2` appended) |
| [`commit-demo-output.txt`](./commit-demo-output.txt) | Full transcript of the demo as it was actually run — including the `git commit -m` that **fails** with "no changes added to commit", then the `git commit -a -m` that succeeds |
| `history.bundle` | The repo's complete git history (2 commits), packaged as a git bundle |

## Restore the history

```bash
git clone history.bundle commit-demo-restored
cd commit-demo-restored && git log --oneline
```

Which gives the same two commits shown at the end of the transcript:

```
d296577 Add line2
7f0a73b Add notes.txt
```

## The takeaway

`-m` commits **only what is already staged** in the index, so a modification to a tracked file that was never `git add`-ed leaves nothing to commit. `-a` auto-stages every tracked file that has been modified or deleted — but still ignores brand-new untracked files, which always need an explicit `git add`.
