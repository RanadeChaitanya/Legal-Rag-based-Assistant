from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def emergency_hit_to_response(hit: Dict[str, Any], disclaimer: str) -> Dict[str, Any]:
    """Converts an EmergencyGate hit into a response dict that render_response understands."""
    return {
        "status": "emergency",
        "case_type": hit.get("category", "emergency"),
        "title": hit.get("title", "Emergency"),
        "rights": hit.get("rights", []),
        "helplines": hit.get("helplines", []),
        "disclaimer": disclaimer,
    }


def _render_helplines(helplines) -> None:
    if not helplines:
        return
    table = Table(title="Helplines")
    table.add_column("Service", style="cyan")
    table.add_column("Number", style="bold yellow")
    for h in helplines:
        table.add_row(Text(str(h.get("name", ""))), Text(str(h.get("number", ""))))
    console.print(table)


def render_response(res: Dict[str, Any]) -> None:
    """Renders formatted legal assistant responses. All dynamic text goes through rich Text so
    brackets in statute/LLM output can never be parsed as markup."""
    status = res.get("status")

    if status == "emergency":
        body = Text()
        body.append("Seek immediate safety or legal representation.\n\n", style="bold")
        for right in res.get("rights", []):
            body.append(f"\u2022 {right}\n")
        console.print(Panel(body, title=Text(f"EMERGENCY: {res.get('title', '')}", style="bold red"),
                            border_style="red"))
        _render_helplines(res.get("helplines"))
        console.print(Text(f"\n{res.get('disclaimer', '')}\n", style="dim"))
        return

    if status == "needs_info":
        body = Text("More information is needed to give an accurate answer:\n\n")
        for slot in res.get("missing_slots", []):
            body.append(f"\u2022 {slot}\n")
        console.print(Panel(body, title=Text("MORE INFORMATION NEEDED", style="bold yellow"),
                            border_style="yellow"))

    for sec in res.get("sections", []):
        style = "yellow" if status == "abstained" else "green"
        console.print(Panel(Text(sec.get("content", "")),
                            title=Text(str(sec.get("heading", "")), style=f"bold {style}"),
                            border_style=style))
        cites = sec.get("citations") or []
        if cites:
            cite_text = Text("Sources:\n", style="bold")
            for c in cites:
                cite_text.append(f"\u2022 {c.get('ref')}: \u201c{c.get('quote')}\u201d\n", style="dim")
            console.print(cite_text)

    timelines = res.get("computed_timelines") or {}
    if timelines:
        table = Table(title="Calculated Statutory Timelines")
        table.add_column("Rule / Event", style="cyan")
        table.add_column("Details", style="magenta")
        for k, v in timelines.items():
            table.add_row(Text(str(k)), Text(str(v)))
        console.print(table)

    _render_helplines(res.get("helplines"))
    console.print(Text(f"\n{res.get('disclaimer', '')}\n", style="dim"))
