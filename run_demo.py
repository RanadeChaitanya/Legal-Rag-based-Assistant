"""
Legal RAG Assistant (India) - Standalone Demo Script
Demonstrates all working modules:
  1. Offline Emergency Gate & Rich UI Rendering
  2. Ingestion Text Cleaning & Chunk Payload Creation
  3. PII Redaction & Sandboxed Evidence Fencing
  4. Grounding Verifier (Fail-Closed 5-Point Citation Check)
  5. Interactive Query Loop
"""

from emergency.gate import EmergencyGate
from cli.render import emergency_hit_to_response, render_response
from ingest.clean import clean_for_embedding
from ingest.chunk import create_structured_chunk
from server.safety import redact_pii, fence_evidence
from server.verifier import GroundingVerifier, build_abstain_response
from rich.console import Console
from rich.panel import Panel

console = Console()


def demo_emergency_gate():
    console.print("\n[bold cyan]=== DEMO 1: Offline Emergency Gate ===[/bold cyan]")
    gate = EmergencyGate()
    
    query = "My brother was arrested by police without any warrant"
    console.print(f"Query: [bold white]\"{query}\"[/bold white]")
    
    hit = gate.evaluate(query)
    if hit:
        res = emergency_hit_to_response(hit, disclaimer="General legal information only — not legal advice.")
        render_response(res)
    else:
        console.print("[yellow]No emergency detected.[/yellow]")


def demo_ingestion():
    console.print("\n[bold cyan]=== DEMO 2: Ingestion & Text Cleaning ===[/bold cyan]")
    raw_text = "[Explanation] ***** Cheque dishonoured for insufficiency of funds in the account."
    
    cleaned = clean_for_embedding(raw_text)
    chunk = create_structured_chunk(
        doc_id="NI Act",
        ref="ni:sec_138",
        hierarchy_path=["Chapter XVII", "Dishonour of Cheques"],
        heading="Dishonour of cheque for insufficiency, etc., of funds in the account",
        text_raw=raw_text,
        applies="current"
    )
    
    console.print(f"Raw Text:      [dim]{raw_text}[/dim]")
    console.print(f"Cleaned Text:  [green]{cleaned}[/green]")
    console.print(f"Chunk ID:      [yellow]{chunk['chunk_id']}[/yellow]")
    console.print(f"Embedding Pfx: [magenta]{chunk['embedding_text']}[/magenta]")


def demo_safety_and_privacy():
    console.print("\n[bold cyan]=== DEMO 3: PII Redaction & Sandboxed Evidence Fencing ===[/bold cyan]")
    user_input = "My phone is +91 9876543210, email is test@legal.in, PAN ABCDE1234F"
    redacted = redact_pii(user_input)
    
    console.print(f"Original Input: [dim]{user_input}[/dim]")
    console.print(f"Redacted Input: [green]{redacted}[/green]\n")
    
    chunks = [{
        "chunk_id": "bnss:sec_58#0",
        "ref": "bnss:sec_58",
        "text_raw": "Person arrested to be taken before Magistrate within twenty-four hours."
    }]
    fenced = fence_evidence(chunks)
    console.print("[bold yellow]Fenced Evidence Sandbox (Prevents Prompt Injection):[/bold yellow]")
    console.print(Panel(fenced, border_style="blue"))


def demo_grounding_verifier():
    console.print("\n[bold cyan]=== DEMO 4: Grounding Verifier (Fail-Closed) ===[/bold cyan]")
    evidence_chunks = [{
        "chunk_id": "bnss:sec_58#0",
        "ref": "bnss:sec_58",
        "text_raw": "Person arrested to be taken before Magistrate within twenty-four hours of arrest."
    }]
    
    verifier = GroundingVerifier(evidence_chunks)
    
    # Valid verified response
    valid_sections = [{
        "heading": "Right to be Produced Within 24 Hours",
        "content": "The arrested person must be taken before a Magistrate within twenty-four hours of arrest.",
        "citations": [{
            "chunk_id": "bnss:sec_58#0",
            "ref": "bnss:sec_58",
            "quote": "taken before Magistrate within twenty-four hours"
        }]
    }]
    
    result = verifier.verify_answer(valid_sections)
    console.print(f"Verification Result (Valid Citation): [bold green]{result.ok}[/bold green]")
    
    # Invalid response (hallucinated quote)
    invalid_sections = [{
        "heading": "Fabricated Timeline",
        "content": "The person can be detained for 72 hours without Magistrate order.",
        "citations": [{
            "chunk_id": "bnss:sec_58#0",
            "ref": "bnss:sec_58",
            "quote": "detained for 72 hours without Magistrate order"
        }]
    }]
    
    bad_result = verifier.verify_answer(invalid_sections)
    console.print(f"Verification Result (Hallucinated Quote): [bold red]{bad_result.ok}[/bold red]")
    console.print(f"Failures: [dim]{bad_result.failures}[/dim]")
    
    if not bad_result.ok:
        console.print("\n[bold yellow]Generating Safe Abstain Response:[/bold yellow]")
        abstain = build_abstain_response(
            evidence_chunks,
            disclaimer="General legal information only. See DISCLAIMER.md.",
            failures=bad_result.failures
        )
        render_response(abstain)


def interactive_mode():
    console.print("\n[bold cyan]=== DEMO 5: Interactive Query Evaluator ===[/bold cyan]")
    console.print("Type any query to test the Emergency Gate (or press Enter to exit):\n")
    
    gate = EmergencyGate()
    while True:
        try:
            query = input("Legal Assistant Query > ").strip()
            if not query:
                break
            hit = gate.evaluate(query)
            if hit:
                res = emergency_hit_to_response(hit, disclaimer="General legal info only.")
                render_response(res)
            else:
                console.print("[yellow]No emergency keyword matched. (Requires vector retrieval for non-emergency questions)[/yellow]\n")
        except (KeyboardInterrupt, EOFError):
            break


def main():
    console.print("[bold green]Legal RAG Assistant - System Overview & Module Demo[/bold green]", justify="center")
    demo_emergency_gate()
    demo_ingestion()
    demo_safety_and_privacy()
    demo_grounding_verifier()
    interactive_mode()


if __name__ == "__main__":
    main()
