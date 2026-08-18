# Failure examples

This page shows what each validation looks like when it fails, and how to fix it.

## Trailing whitespace

```text
trim trailing whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1
- files were modified by this hook

Fixing docs/index.md
```

**Fix:** the hook rewrites the file for you. Re-stage and commit again:

```bash
git add -u && git commit
```

## Missing newline at end of file

```text
fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook

Fixing mkdocs.yml
```

**Fix:** auto-repaired. Re-stage and commit.

## Invalid YAML

```text
check yaml...............................................................Failed
- hook id: check-yaml
- exit code: 1

mkdocs.yml
  while scanning a simple key
  expected ':', but found a stream end
  in "mkdocs.yml", line 12, column 3
```

**Fix:** correct the indentation or the missing `:` at the reported line. This hook is
what stops a malformed `mkdocs.yml` or workflow file from ever reaching CI.

## Unresolved merge conflict

```text
check for merge conflicts................................................Failed
- hook id: check-merge-conflict
- exit code: 1

docs/index.md:14: Merge conflict string '<<<<<<<' found
```

**Fix:** finish the merge, delete the `<<<<<<<` / `=======` / `>>>>>>>` markers, then
re-stage.

## Oversized file

```text
check for added large files..............................................Failed
- hook id: check-added-large-files
- exit code: 1

docs/assets/demo.mp4 (4821 KB) exceeds 512 KB.
```

**Fix:** compress the asset, or host it externally and link to it. Do not raise the
limit to sneak a binary into git history — it stays there forever.

## Markdown style

```text
markdownlint-cli2........................................................Failed
- hook id: markdownlint-cli2
- exit code: 1

docs/index.md:7 MD022/blanks-around-headings Headings should be surrounded by blank lines
docs/index.md:9 MD012/no-multiple-blanks Multiple consecutive blank lines
```

**Fix:** apply the change the rule name describes. Rules we deliberately disable
(`MD013` line length, `MD033` inline HTML) live in `.markdownlint-cli2.yaml`.

## Spelling

```text
codespell................................................................Failed
- hook id: codespell
- exit code: 65

docs/validation.md:18: recieve ==> receive
```

**Fix:** correct the typo. For a false positive — a deliberate term or a proper noun —
add the word on its own line in `.codespellignore`.

## Broken docs build

This is the one that most often catches real breakage, because `--strict` promotes
MkDocs warnings to errors.

```text
mkdocs build --strict....................................................Failed
- hook id: mkdocs-build-strict
- exit code: 1

ERROR   -  Doc file 'validation.md' contains a link 'failures.md', but the target
           is not found among documentation files.
Aborted with a build error!
```

Other common `--strict` failures:

| Message | Cause |
| --- | --- |
| `The following pages exist in the docs directory, but are not included in the "nav"` | New page not added to `nav:` in `mkdocs.yml` |
| `contains a link '...', but the target is not found` | Renamed or deleted page still linked |
| `Config value 'theme': Unrecognised theme name` | Theme dependency missing from `requirements-docs.txt` |

**Fix:** reproduce it locally with the exact command CI uses:

```bash
mkdocs build --strict
```

## Reproducing CI locally

The GitHub Actions `validate` job runs nothing more than this:

```bash
pre-commit run --all-files --show-diff-on-failure
```

If that is green on your machine, the deploy will proceed.
