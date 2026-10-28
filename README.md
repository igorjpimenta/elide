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
elide [--width N | --width-file PATH] [--ellipsis STR] [--words] [--pad]
      [FILE ...]
```

With no `FILE` arguments, `elide` reads stdin. With one or more `FILE`
arguments, it reads each file in order and writes all output lines to
stdout.

### `--width-file PATH`

Reads the max display width from the first non-empty line of the file at
`PATH`, so the width can be changed without editing the command line.
Leading blank lines are skipped and the line is stripped, so trailing
whitespace or a CRLF ending on that line are fine. Takes the same
validation as `--width` (positive integer) and is mutually exclusive
with it (exit 2 if both are given). Errors — file missing, directory,
empty, contents not a positive integer — exit 2.

## Flag reference

| Flag | Default | Meaning |
| --- | --- | --- |
| `--width N` | `40` | Max display width per line. Exit 2 if not an integer, `<= 0`, or narrower than the ellipsis's display width. |
| `--width-file PATH` | none | Max display width read from the first non-empty line of the file at `PATH` (stripped, CRLF-safe). Mutually exclusive with `--width`. Errors exit 2. |
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

# 8. Width read from a file (first non-empty line: "10")
printf '10\n' > /tmp/elide-width.txt
printf 'abcdefghij\n' | elide --width-file /tmp/elide-width.txt   # "abcdefghij"

# 9. Width file skips leading blank lines
printf '\n\n5\n' > /tmp/elide-width2.txt
printf 'hello world\n' | elide --width-file /tmp/elide-width2.txt   # "hell…"

# 10. CRLF input: cut without a stray CR
printf 'hello world\r\nsecond\r\n' | elide --width 5   # "hell…\nseco…"
```

## `--pad` and `--words` together

In word-boundary mode the line may end shorter than expected even
before padding; `--pad` fills exactly to `--width` regardless.

## CRLF handling

CRLF (`\r\n`) input never leaks a `\r` into the output. Lines pass
through, cut, or pad identically to LF-only input:

```text
$ printf 'hello world\r\nsecond\r\n' | elide --width 5
hell…
seco…
$ printf 'hello world\r\n' | elide --width 12 --pad
hello world 
```

## Width-file errors

All exit 2. A usage block precedes each error message on stderr (shown
for the last example). Error lines observed verbatim:

```text
$ printf 'abc\n' > w5.txt && printf 'hello\n' | elide --width-file w5.txt
elide: error: --width-file must contain a positive integer
$ elide --width-file /tmp/elide-width-empty.txt            # file blank
elide: error: --width-file /tmp/elide-width-empty.txt: file is empty
$ elide --width-file /tmp/missing-width.txt
elide: error: --width-file /tmp/missing-width.txt: No such file or directory
$ elide --width 5 --width-file /tmp/elide-width.txt
usage: elide [-h] [--width WIDTH | --width-file PATH] [--ellipsis ELLIPSIS]
             [--words] [--pad]
             [FILE ...]
elide: error: argument --width-file: not allowed with argument --width
```

## Exit codes

- `0` — success.
- `1` — a file could not be read (missing, directory, OS error);
  stderr names each failing file, other files still process.
- `2` — invalid arguments: `--width` (or the first line of
  `--width-file`) not an integer, `<= 0`, or the ellipsis wider than
  `--width` by display width; also on mutually exclusive
  `--width` + `--width-file`, and width-file read errors
  (missing, directory, empty) — see Width-file errors above.

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
