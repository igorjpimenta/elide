# elide

Truncate each input line to a max display width.

## Usage

```
elide [--width N] [--ellipsis STR] [--words] [--pad] [FILE ...]
```

- `--width N` (default 40): max display width per line.
- `--ellipsis STR` (default `…`): appended when a line is cut; truncation
  reserves space so total display width stays within `--width`.
- `--words`: cut on a word boundary instead of mid-word (falls back to a
  hard cut when no boundary fits).
- `--pad`: pad short lines with spaces to exactly `--width` columns.
- Reads stdin when no files are given, else reads each file in order.

Wide (East Asian) characters count as width 2; combining marks are
best-effort. Invalid `--width` (non-integer, `<= 0`, or narrower than the
ellipsis) exits with code 2.

## Examples

```sh
echo hello | elide --width 3        # he…
echo "hello world" | elide --width 10 --words
printf 'hi\n' | elide --width 5 --pad
```

No dependencies beyond the Python 3 standard library. `elide` is a single
executable script.
