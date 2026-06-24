# Yonakh Research Paper

**Title:** "Yonakh: A Shared Memory Architecture for Multi-Agent AI-Assisted Software Development"

**Target:** [IEEE Software](https://www.computer.org/csdl/magazine/so) (IEEE Computer Society)

**Code:** [github.com/shvenkat/yonakh](https://github.com/shvenkat/yonakh)

## Files

| File | Description |
|------|-------------|
| `yonakh-journal.tex` | Full journal article (IEEE Software format) |
| `references.bib` | BibTeX bibliography (42 citations) |
| `README.md` | This file |

## Compilation

### Prerequisites

Install TeX Live (or BasicTeX on macOS):

```bash
# macOS (Homebrew)
brew install --cask mactex
# or minimal: brew install --cask basictex

# Ubuntu/Debian
sudo apt-get install texlive-full

# Fedora
sudo dnf install texlive-scheme-full
```

### Build PDF

```bash
cd paper

# IEEE Software format
pdflatex yonakh-journal.tex
bibtex yonakh-journal
pdflatex yonakh-journal.tex
pdflatex yonakh-journal.tex
```

Or use latexmk:
```bash
latexmk -pdf yonakh-journal.tex
```

### Overleaf

Upload files to [Overleaf](https://www.overleaf.com) for online compilation. The IEEEtran class is built into Overleaf.

---

## Abstract

AI coding assistants (Claude Code, Cursor, Copilot, Codex) are transforming software development, yet each tool maintains isolated, ephemeral memory. This *memory fragmentation* undermines effectiveness: decisions recorded in one session are invisible to another; failed debugging attempts are repeated; design rationale evaporates between conversations.

**Yonakh** provides a shared, local-first memory server with:
- Knowledge graph ontology (21 entity types, 21 relationship types)
- Memory quality model (importance scoring, temporal decay, conflict detection)
- Hybrid search (FTS + semantic via Reciprocal Rank Fusion)
- Rules engine for automated relationship inference
- Full provenance with time-travel queries
- REST API + MCP integration for tool interoperability

## Contributions

1. **Domain Ontology** - 21 entity types (decisions, bugs, failed attempts, design rationale, commits, etc.) and 21 relationship types (supersedes, contradicts, implements, reverts, etc.)

2. **Memory Quality Model** - Multi-signal importance scoring, temporal decay with domain-specific half-lives, automated conflict detection

3. **Open Architecture** - REST API and Model Context Protocol (MCP) enabling memory sharing across heterogeneous AI tools

4. **Theoretical Foundation** - Grounding in cognitive science (memory systems) and knowledge management theory (SECI model, transactive memory)

## Key Citations

- **ADRs:** Nygard (2011), Soldani et al. (ECSA 2024), Tofan et al. (2023)
- **Knowledge Loss:** Rigby et al. (ICSE 2016), Nassif & Robillard (ESEC/FSE 2021)
- **Code Knowledge Graphs:** CodexGraph (2024), CGM (2025)
- **LLM Agent Memory:** HiAgent (ACL 2025), HMAT (ICLR 2026), CAT (ACL Findings 2026)
- **Hybrid Search:** Cormack et al. RRF (SIGIR 2009)
- **Cognitive Science:** Baddeley (2012), Tulving (1985), Nonaka & Takeuchi (1995)
