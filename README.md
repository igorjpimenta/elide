# elide

Truncate each input line to a maximum display width.

`elide` reads lines from stdin (or files), cuts each line that exceeds the
maximum width, and appends an ellipsis to every line it cut. Line counting
uses terminal display width, so East Asian wide characters correctly count
as 2 columns, and combining marks add nothing.

## Install

Download the single `elide` script (Python 3, standard library only) from
this repository and make it executable:

```sh
git clone https://github.com/igorjpimenta/elide.git
cd elide
chmod +x elide
./elide --help
```

No pip install, no dependencies.

## Usage

```
elide [--width N] [--ellipsis STR] [--words] [--pad] [FILE ...]
```

With no `FILE` arguments, `elide` reads stdin. With one or more `FILE`
arguments, it reads each file in order and writes all output lines to
stdout.

## Flag reference

| Flag | Default | Meaning |
| --- | --- | --- |
| `--width N` | `40` | Max display width per line. Exit 2 if not an integer, `<= 0`, or narrower than the ellipsis's display width. |
| `--ellipsis STR` | `…` | String appended when a line is cut. Exit 2 if its display width exceeds `--width`. An empty string is valid. |
| `--words` | off | Cut on a word boundary when one fits inside the width. |
| `--pad` | off | Pad short lines with spaces to exactly `--width` columns. |

### Truncation semantics

When a line is cut, the ellipsis's own display width is subtracted from
the budget first, so total line width never exceeds `--width`. The
empty ellipsis is valid: `--ellipsis ''` cuts without a marker.

### `--words` boundary rules

`--words` prefers the boundary nearest the cut; if the resulting trimmed
word is nonempty, that becomes the line. When the input has no word
boundary at all (a single long word), `elide` hard-cuts at the width,
like plain non-word mode.

## Wide characters

East Asian Wide/Fullwidth characters count as display width 2, so
truncation happens by *display* width, not character count. Combining
marks (e.g. `é` built from `e` + U+0301) are best-effort ignored: they
count 0 toward width and stay attached to their base character when
cut points land near them.

## Examples

```sh
# 1. Default width 40, default ellipsis
echo hello | elide

# 2. Mid-word cut at 5 columns (default behavior without --words)
printf 'a\nhello world\n' | elide --width 5   # "a\nhell…"

# 3. Word-boundary cut at 10 columns
printf 'hello world foo\n' | elide --width 10 --words   # "hello…"

# 4. Pad short lines to exactly the width
printf 'hi\n' | elide --width 5 --pad   # "hi   "

# 5. Work from a file, not stdin
printf 'line one\nline two\n' > /tmp/elide-in.txt
elide /tmp/elide-in.txt --width 7   # "line o…" per line

# 6. East Asian wide chars
printf 'こんにちはworld\n' | elide --width 9   # "こんにち…"

# 7. Custom ellipsis string
printf 'hello world\n' | elide --width 8 --ellipsis '...'   # "hello..."
```

## `--pad` and `--words` together

In word-boundary mode the line may end shorter than expected even
before padding; `--pad` fills exactly to `--width` regardless.

## Exit codes

- `0` — success.
- `1` — a file could not be read (missing, directory, OS error);
  stderr names each failing file, other files still process.
- `2` — invalid arguments: `--width` not an integer, `<= 0`, or the
  ellipsis wider than `--width` by display width.

```sh
$ elide --width abc
elide: error: --width must be a positive integer      # exit 2
$ elide --width 0
elide: error: --width must be a positive integer      # exit 2
$ elide --width 3 --ellipsis "abcd"
elide: error: ellipsis display width exceeds --width  # exit 2
$ elide --width 1 --ellipsis "…"
# legal: "…" has display width 1                     # exit 0
$ elide /tmp/missing.txt
elide: /tmp/missing.txt: No such file or directory    # exit 1
```

## SEE ALSO

`fold(1)` — hard-wraps long lines at an exact byte/character count.
`cut(1)` — extracts exact column ranges from each line, no width awareness.
