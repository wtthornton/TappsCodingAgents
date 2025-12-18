# Flattener Guide (BMAD)

BMAD supports generating a single “flattened” view of a repository to make it easier to paste/upload into tools with limited multi-file context.

## Command

From your project root:

```bash
npx bmad-method flatten
```

## Output

The exact output file name/location depends on the BMAD CLI version, but it is typically a single XML/markdown file that concatenates the codebase with paths and separators.

## Notes

- Use this for **brownfield** projects when your AI tool cannot access the repo directly.
- Treat the flattened file as sensitive: it can contain proprietary code. Avoid sharing it outside approved environments.


