#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flatten_paths.py - strip folder-structure references from every .py and .json file in the
folder you run it from (not recursive).

    python flatten_paths.py              # modify files in place (a .bak copy of each is kept)
    python flatten_paths.py --dry-run    # only show what would change
    python flatten_paths.py --no-backup  # modify without keeping .bak copies

What it changes
  * path-like text inside Python strings/comments and anywhere in JSON files:
        "01_Proj/analysis/out.xlsx" -> "out.xlsx"      "..\\\\data\\\\x.json" -> "x.json"
        "../"  -> ""                                    "C:\\\\dir\\\\sub\\\\" -> ""
  * os.path.join(...) calls in Python: folder-name string arguments are dropped
        os.path.join(HERE, "morphology", "run.py") -> os.path.join(HERE, "run.py")
        os.path.join(HERE, "..")                   -> os.path.join(HERE)

What it leaves alone (review these by hand)
  * raw strings (r"..."), bytes and f-strings; pathlib code (Path(a) / "sub" / "f")
  * a lone folder name with no extension, e.g. os.path.join(HERE, "data"), because it cannot
    tell a folder from a file
  * URLs, dates, and slash-separated prose (a/b/c) unless it has a file extension, a leading
    ./ ../ / or drive letter, or underscores/digits in a multi-level chain

Every edit is printed (file:line old -> new). Edited files are re-checked (compile / json.loads)
and left untouched if the result would be invalid. This script never edits itself.
"""
import argparse
import ast
import io
import json
import os
import re
import shutil
import tokenize

SEP = r"(?:/|\\\\)"   # '/' or two backslash characters (an escaped '\' in Python/JSON source text)
SEG = r"[^\s/\\\"'`<>|:*?{}()\[\],;=+^$!&%@#~]+"
SEP_RE = re.compile(SEP)
PATH = re.compile(
    r"(?<![^\s\"'(\[{,;=<>`|])"
    r"(?P<p>(?:[A-Za-z]:)?" + SEP + "?" + SEG + "(?:" + SEP + SEG + ")*" + SEP + "?)"
)


def flatten(p):
    """Return the replacement for a path-like match, or None if it does not look like a path."""
    drive = re.match(r"[A-Za-z]:", p)
    body = p[drive.end():] if drive else p
    seps = SEP_RE.findall(body)
    if not seps:
        return None
    parts = [x for x in SEP_RE.split(body) if x]
    absolute = bool(drive) or body.startswith("/")
    relative = bool(parts) and parts[0] in (".", "..")
    has_ext = bool(parts) and re.fullmatch(r".+\.[A-Za-z]\w{0,4}", parts[-1]) is not None
    deep = len(seps) >= 2 and any(re.search(r"[\d_]", x) for x in parts)   # a/b_c/d style folder chain
    if not (absolute or relative or has_ext or deep):
        return None
    if parts and all(x.isdigit() for x in parts):      # dates / fractions
        return None
    if SEP_RE.fullmatch(body[-1:]) or body.endswith("\\\\"):   # ends with a separator: folder only
        return ""
    last = parts[-1] if parts else ""
    return "" if last in (".", "..") else last


def fix_text(text, first_row=1):
    changes = []

    def repl(m):
        p = m.group("p")
        core = p.rstrip(".")
        tail = p[len(core):]
        new = flatten(core)
        if new is None:
            return p
        changes.append((first_row + text.count("\n", 0, m.start()), core, new))
        return new + tail

    return PATH.sub(repl, text), changes


# ---------------------------------------------------------------- python
def fix_py_strings(src):
    offs = [0]
    for line in src.split("\n"):
        offs.append(offs[-1] + len(line) + 1)
    edits, changes = [], []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.STRING:
            prefix = re.match(r"[A-Za-z]*", tok.string).group().lower()
            if set(prefix) & set("rbf"):
                continue
        elif tok.type != tokenize.COMMENT:
            continue
        new, ch = fix_text(tok.string, tok.start[0])
        if ch:
            start = offs[tok.start[0] - 1] + tok.start[1]
            edits.append((start, start + len(tok.string), new))
            changes += ch
    for s, e, new in sorted(edits, reverse=True):
        src = src[:s] + new + src[e:]
    return src, changes


def _is_join(node):
    f = node.func
    return (isinstance(f, ast.Attribute) and f.attr == "join" and not node.keywords and
            ((isinstance(f.value, ast.Attribute) and f.value.attr == "path") or
             (isinstance(f.value, ast.Name) and f.value.id in ("path", "posixpath", "ntpath"))))


def _kept_args(args):
    keep, n = [], len(args)
    for i, a in enumerate(args):
        lit = isinstance(a, ast.Constant) and isinstance(a.value, str)
        if lit and (a.value in ("..", ".") or i < n - 1):
            continue
        keep.append(a)
    return keep


def fix_py_joins(src):
    changes = []
    for _ in range(1000):
        target = None
        for node in ast.walk(ast.parse(src)):          # outermost calls first
            if isinstance(node, ast.Call) and _is_join(node):
                keep = _kept_args(node.args)
                if len(keep) != len(node.args):
                    target = (node, keep)
                    break
        if target is None:
            break
        node, keep = target
        old = ast.get_source_segment(src, node)
        if keep:
            func = ast.get_source_segment(src, node.func)
            new = f"{func}({', '.join(ast.get_source_segment(src, a) for a in keep)})"
        else:
            new = '""'
        b = src.encode("utf-8")
        offs = [0]
        for line in b.split(b"\n"):
            offs.append(offs[-1] + len(line) + 1)
        s = offs[node.lineno - 1] + node.col_offset
        e = offs[node.end_lineno - 1] + node.end_col_offset
        src = (b[:s] + new.encode("utf-8") + b[e:]).decode("utf-8")
        changes.append((node.lineno, " ".join(old.split()), new))
    return src, changes


def process_py(text):
    text, c1 = fix_py_strings(text)
    text, c2 = fix_py_joins(text)
    compile(text, "<result>", "exec")
    return text, c1 + c2


def process_json(text):
    new, ch = fix_text(text)
    json.loads(new)
    return new, ch


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Remove folder-structure references from .py and .json "
                                             "files in the current folder.")
    ap.add_argument("--dry-run", action="store_true", help="show changes without writing anything")
    ap.add_argument("--no-backup", action="store_true", help="do not keep a .bak copy of changed files")
    a = ap.parse_args()

    here = os.getcwd()
    me = os.path.abspath(__file__)
    files = sorted(f for f in os.listdir(here)
                   if f.lower().endswith((".py", ".json")) and os.path.isfile(os.path.join(here, f))
                   and os.path.abspath(os.path.join(here, f)) != me)
    if not files:
        print("No .py or .json files found in", here)
        return
    total = 0
    for name in files:
        path = os.path.join(here, name)
        with open(path, "rb") as fh:
            raw = fh.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"{name}: SKIPPED (not UTF-8)")
            continue
        bom = text.startswith("\ufeff")
        if bom:
            text = text[1:]
        try:
            new, changes = (process_py if name.lower().endswith(".py") else process_json)(text)
        except Exception as exc:                      # syntax error, invalid result, ...
            print(f"{name}: SKIPPED ({type(exc).__name__}: {exc})")
            continue
        if new == text:
            print(f"{name}: no folder references found")
            continue
        print(f"{name}: {len(changes)} change(s)")
        for row, old, repl in sorted(changes, key=lambda c: c[0]):
            print(f"  line {row}: {old!r} -> {repl!r}")
        total += len(changes)
        if a.dry_run:
            continue
        if not a.no_backup and not os.path.exists(path + ".bak"):
            shutil.copy2(path, path + ".bak")
        with open(path, "wb") as fh:
            fh.write((("\ufeff" if bom else "") + new).encode("utf-8"))
    print(f"\n{total} change(s) {'found (dry run, nothing written)' if a.dry_run else 'written'}.")


if __name__ == "__main__":
    main()
