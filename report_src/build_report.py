"""Fill report.md placeholders from repo files and render report.pdf (pandoc + pdflatex)."""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def section(name: str) -> str:
    p = HERE / f"{name}.md"
    return p.read_text().strip() if p.exists() else f"*({name}: pending)*"


def adr_table() -> str:
    rows = []
    for line in (ROOT / "architecture/decisions/README.md").read_text().splitlines():
        m = re.match(r"^\| \[(\d+)\]\(ADR-\d+\.md\) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$", line)
        if m:
            n, dec, chosen, rej, why, st = m.groups()
            rows.append(f"| {n} | {dec} | {chosen} | {rej} | {why} | {st} |")
    return ("Table: All ADRs (full text in `architecture/decisions/`).\n\n"
            "| ADR | Decision | Chosen | Main option rejected | Main reason | Status |\n"
            "|---|------|--------|-------|-------|---|\n" + "\n".join(rows))


STAGES = """Table: Stage map: agent, artifact and the code check per stage (full version with inputs and withheld inputs in `architecture/views/stage-map.md`).

| # | Stage | Agent / component (model) | Artifact | Check, decided by code | On failure |
|---|---|------|---|--------|------|
| 1 | Requirements | Analyst (flash-lite) | `spec.md` | parses; 1-6 `AC-n`, each Given/When/Then; fuzzy-word lint on *Then* | retry with gate feedback (2x), then stop |
| 2 | Design | Analyst (flash-lite) | `design.md` | Changes table; every MODIFY `file::Class.method` exists per AST | retry (2x), then stop |
| 3 | Implementation | Builder (flash-lite) | `diff.patch` | diff touches only `tinydb/`; compileall, import, `mypy` in sandbox | retry within budget of 3 |
| 4 | Testing | Tester (flash-lite) | `test_report.md` | each AC has `test_acN_*`; **red on base, green on head**; full suite green | test fault: Tester rewrites; code fault: back to 3; 3 fails: back to 2 once; then stop |
| 5 | Release | `ship_*` script (no LLM) | `pr.md` + PR link | PR open; pytest + mypy on PR head = commit status `autose/ci` | stop, reason in ledger |
| 6 | Review | Reviewer (3-flash-preview) | `review.md` | approval needs executed commands; findings need evidence | approach: back to 2; code: back to 3; max 2 rounds; human decides |"""


def main():
    t = (HERE / "report.md").read_text()
    fills = {"{{STAGE_TABLE}}": STAGES, "{{ADR_TABLE}}": adr_table()}
    for k in ("SEQUENCE", "EXPERIMENTS", "RESULTS", "HINDSIGHT", "LIMITATIONS", "RUNS"):
        fills["{{" + k + "}}"] = section(k.lower())
    for k, v in fills.items():
        t = t.replace(k, v)
    for a, b in {"✓": "(ok)", "✗": "(x)", "→": "->", "≤": "$\\le$", "≥": "$\\ge$", "…": "...",
                 "×": "x", "–": "--", "—": "---", "‘": "'", "’": "'", "“": '"', "”": '"', "🛑": "", "✅": "", "⏳": ""}.items():
        t = t.replace(a, b)
    out = HERE / "report.filled.md"
    out.write_text(t)
    subprocess.run(["pandoc", str(out), "-o", str(ROOT / "report.pdf"), "--pdf-engine=pdflatex",
                    "-V", "tables=true", "--resource-path", str(HERE)], check=True, cwd=HERE)
    pages = subprocess.run(["pdfinfo", str(ROOT / "report.pdf")], capture_output=True, text=True).stdout
    print([l for l in pages.splitlines() if l.startswith("Pages")])


if __name__ == "__main__":
    main()
