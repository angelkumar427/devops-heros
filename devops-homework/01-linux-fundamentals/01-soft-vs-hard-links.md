# Soft Links vs Hard Links

## The core difference

| | Hard Link | Soft (Symbolic) Link |
|---|---|---|
| What it points to | The same **inode** (the actual data on disk) as the original file | The **path/name** of the original file |
| Works across filesystems/partitions? | No — must be on the same filesystem | Yes |
| Can link to a directory? | No (not allowed by most filesystems) | Yes |
| What happens if the original is deleted? | Still works — the data stays alive as long as at least one hard link (link count > 0) references it | Breaks — becomes a "dangling" link, since the path it pointed to no longer resolves |
| File size shown by `ls -l` | Same as the original (it *is* the original data) | Size of the path string it stores |
| Identified by | Same inode number as the original (`ls -li`) | `l` in the permissions column and a `name -> target` arrow in `ls -l` |

In short: a hard link is another name for the exact same file on disk. A soft link is a small separate file that just contains a pointer to another path — conceptually like a Windows shortcut.

## Commands

```bash
# Create a hard link
ln original.txt hardlink.txt

# Create a soft/symbolic link
ln -s original.txt softlink.txt
ln -s /absolute/path/to/target linkname   # symlinks are usually made with absolute paths

# Delete a link (this never deletes the underlying data unless it's the last hard link)
rm hardlink.txt
rm softlink.txt

# Inspect links
ls -li          # -i shows inode numbers; hard links to the same file share an inode
readlink softlink.txt   # show what a symlink points to
stat original.txt       # shows "Links: N" = how many hard links reference this inode
```

## Hands-on demo (actually run — see `linkdemo-output.txt` in this folder)

Steps performed:
1. Created `original.txt` with some content.
2. `ln original.txt hardlink.txt` → hard link.
3. `ln -s original.txt softlink.txt` → soft link.
4. `ls -li` showed `hardlink.txt` and `original.txt` sharing the **same inode number**, while `softlink.txt` has its own inode and shows `softlink.txt -> original.txt`.
5. Deleted `original.txt`.
6. `cat hardlink.txt` still printed the file content — the hard link kept the data alive.
7. `cat softlink.txt` failed with `No such file or directory` — the symlink pointed at a path that no longer exists (broken link).

Full transcript with real command output: [`linkdemo-output.txt`](./linkdemo-output.txt)

## Interview-style talking points

- "A hard link *is* the file; a soft link *points to* the file."
- Deleting a file just decrements its link count; the data is only actually freed when the link count hits zero **and** no process has it open.
- Soft links can dangle (point to nothing); hard links can't — you can't even create one to a nonexistent file.
- Hard links can't cross filesystem boundaries because inode numbers are only unique within a single filesystem; symlinks can, because they're just stored text paths.
- `du` vs `ls -l` on symlinks can be confusing: `ls -l` on the link shows the tiny size of the path string, but following the link (`ls -lL`) shows the target's real size.
