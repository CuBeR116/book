# Repository Guidelines

## Project Structure & Module Organization

This repository contains Russian dark-fantasy manuscripts and worldbuilding, rather than a conventional application.

- `Манхва/Книга/Главы/`: authoritative chapter text; `_служебное/собрать_docx.py` assembles the book.
- `Манхва/Книга/`: character canon, POV voices, tone, geography, language, plot plans, and incoming ideas.
- `Obsidian/Имя, которого быть не должно/`: world, character, arc, and magic-system wiki.
- `Заклинания/Конструктор.html`: standalone HTML/CSS/JavaScript magic-circle editor, with JSON configurations and SVG assets.
- `Манхва/Книга/_архив/`: historical drafts; consult only when requested.
- `Игра/`: separately versioned `book-game` project, ignored here; follow its own instructions.

Illustrations, Krita/Blender sources, DOCX files, and `_Для телефона/` bundles remain local in Yandex.Disk and are ignored by Git.

## Build, Test, and Development Commands

Run from the repository root:

- `python "Манхва/Книга/_служебное/собрать_docx.py"`: rebuilds `Манхва/Книга/Том 1 (сборка).docx`; requires the local `Том 1.docx` template and referenced illustrations. Uses Python's standard library.
- Open `Заклинания/Конструктор.html` directly in a browser to use the editor; no installation or bundler is required.
- `git diff --check`: checks whitespace errors before committing.

Use PowerShell for Windows paths. Execute commands involving `/mnt/...` inside Ubuntu WSL, invoking `wsl.exe -d Ubuntu` from Windows when necessary.

## Style & Naming Conventions

Preserve UTF-8, Russian names, existing Markdown headings, paragraph breaks, and Obsidian links. Chapters use two-digit prefixes, such as `01 ПРОБУЖДЕНИЕ.md`; split chapters use `06a` and `06b`. Python uses four-space indentation; preserve the constructor's existing compact style. No formatter or linter configuration is present.

## Validation Guidelines

There is no automated test suite or coverage threshold for this repository. Check manuscript changes against canon, POV voices, and magic-energy costs. Never rewrite completed chapters without an explicit request or silently invent world facts. For assembler changes, rebuild and inspect chapter order, emphasis, and illustrations. For constructor changes, manually verify controls, JSON save/load, and SVG/PNG export.

## Commit & Review Guidelines

Work on `main`; do not create branches. History uses concise Russian topic-prefixed messages, such as `идеи: аннотация для самиздата`. Desktop commits and pushes occur when requested; phone/cloud edits require committing and pushing to `main`. Describe affected files, canon implications, and validation; include screenshots for constructor UI changes. Discuss conflicting chapter versions with the author before resolving them.
