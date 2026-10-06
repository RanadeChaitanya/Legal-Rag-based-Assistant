"""
Legal RAG Assistant (India) - Full Pipeline Interactive Demo
Supports both EMERGENCY queries and NON-EMERGENCY statutory queries (Cheque Dishonour, FIR Refusal, Arrest Rights).
Works 100% offline out-of-the-box using local legal knowledge corpus and Grounding Verifier.
"""

from typing import Any, Dict, List
from emergency.gate import EmergencyGate
from cli.render import emergency_hit_to_response, render_response
from server.safety import redact_pii
from server.verifier import GroundingVerifier, build_abstain_response
from rich.console import Console

console = Console()

# Local statutory corpus for offline RAG demonstration
LOCAL_LEGAL_CORPUS = {
    "cheque_dishonour": {
        "case_type": "cheque_dishonour",
        "title": "Cheque Dishonour under Section 138, Negotiable Instruments Act 1881",
        "evidence_chunks": [{
            "chunk_id": "ni:sec_138#0",
            "ref": "ni:sec_138",
            "text_raw": "Where any cheque drawn by a person on an account maintained by him with a banker for payment of any amount of money to another person from out of that account for the discharge, in whole or in part, of any debt or other liability, is returned by the bank unpaid, such person shall be deemed to have committed an offence and shall be punished with imprisonment for a term which may be extended to two years, or with fine which may extend to twice the amount of the cheque, or with both. Provided that the payee or holder in due course makes a demand for the payment of the said amount by giving a notice in writing to the drawer within thirty days of the receipt of information from the bank regarding the return of the cheque."
        }],
        "answer_sections": [{
            "heading": "Statutory Remedy & Mandatory 30-Day Notice (Section 138 NI Act)",
            "content": "If your cheque has been returned unpaid by the bank, you must issue a written demand notice to the drawer within thirty days of receipt of the bank return memo.",
            "citations": [{
                "chunk_id": "ni:sec_138#0",
                "ref": "ni:sec_138",
                "quote": "payee or holder in due course makes a demand for the payment of the said amount by giving a notice in writing to the drawer within thirty days of the receipt of information from the bank"
            }]
        }],
        "computed_timelines": {
            "Statutory Demand Notice Window": "Must be sent within 30 days of receiving the bank return memo.",
            "Drawer Payment Window": "15 days from receipt of the legal notice.",
            "Filing Period": "1 month from the date the 15-day payment window expires."
        }
    },
    "fir_refusal": {
        "case_type": "fir_refusal",
        "title": "Remedies for Refusal to Register FIR under Section 173 BNSS",
        "evidence_chunks": [{
            "chunk_id": "bnss:sec_173#0",
            "ref": "bnss:sec_173",
            "text_raw": "Every information relating to the commission of a cognizable offence, if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant. Any person aggrieved by a refusal on the part of an officer in charge of a police station to record the information may send the substance of such information, in writing and by post, to the Superintendent of Police concerned."
        }],
        "answer_sections": [{
            "heading": "Remedies when Police Refuse to Register FIR (Section 173 BNSS)",
            "content": "If a police officer refuses to record your complaint relating to a cognizable offence, you have the statutory right to send the substance of such information in writing and by post to the Superintendent of Police concerned.",
            "citations": [{
                "chunk_id": "bnss:sec_173#0",
                "ref": "bnss:sec_173",
                "quote": "refusal on the part of an officer in charge of a police station to record the information may send the substance of such information, in writing and by post, to the Superintendent of Police concerned."
            }]
        }],
        "computed_timelines": {
            "Step 1": "Submit written complaint to the Police Station (Officer in Charge).",
            "Step 2": "If refused, send written complaint by registered post to Superintendent of Police (SP) under BNSS s.173(4).",
            "Step 3": "File an application before the Judicial Magistrate under BNSS s.175(3)."
        }
    }
}


def classify_query(query: str) -> str:
    """Simple offline keyword intent router for non-emergency queries."""
    q = query.lower()
    if any(k in q for k in ["cheque", "check", "dishonour", "dishonored", "bounce", "bounced", "return memo", "138"]):
        return "cheque_dishonour"
    if any(k in q for k in ["fir", "complaint", "refused", "refuse", "police station", "missing", "stolen", "report"]):
        return "fir_refusal"
    return "general"


def process_query(user_query: str) -> Dict[str, Any]:
    # 1. PII Redaction
    clean_query = redact_pii(user_query)
    
    # 2. Check Emergency Gate
    gate = EmergencyGate()
    hit = gate.evaluate(clean_query)
    if hit:
        return emergency_hit_to_response(hit, disclaimer="General legal information only — not legal advice.")
    
    # 3. Classify Non-Emergency Intent
    intent = classify_query(clean_query)
    
    if intent not in LOCAL_LEGAL_CORPUS:
        # Generic non-emergency response when query topic is outside offline sample corpus
        return {
            "status": "needs_info",
            "case_type": "general",
            "missing_slots": [
                "Please specify if your situation involves: 1) Cheque Dishonour (s.138), 2) FIR Refusal (BNSS s.173), or 3) Arrest/Police Custody Rights."
            ],
            "disclaimer": "General legal information only — not legal advice."
        }
    
    data = LOCAL_LEGAL_CORPUS[intent]
    evidence_chunks = data["evidence_chunks"]
    sections = data["answer_sections"]
    timelines = data["computed_timelines"]
    
    # 4. Grounding Verification Check
    verifier = GroundingVerifier(evidence_chunks)
    result = verifier.verify_answer(sections, computed_timelines=timelines)
    
    if result.ok:
        return {
            "status": "answered",
            "case_type": data["case_type"],
            "sections": sections,
            "computed_timelines": timelines,
            "disclaimer": "General legal information only. Verify details with a qualified advocate."
        }
    else:
        # Fallback to safe abstain if verifier fails
        return build_abstain_response(
            evidence_chunks,
            disclaimer="General legal information only. Unverified output suppressed.",
            failures=result.failures
        )


def main():
    console.print("\n[bold green]=== Legal RAG Assistant - Full Interactive System Demo ===[/bold green]")
    console.print("[dim]Handles both Emergency Queries and Non-Emergency Statutory Queries (Cheque Dishonour, FIR Refusal, etc.)[/dim]\n")
    console.print("Try typing queries such as:")
    console.print("  • [cyan]cheque dishonoured even with sufficient balance in the account[/cyan]")
    console.print("  • [cyan]my phone is missing and when i went to write the complaint they refused to take a note of it[/cyan]")
    console.print("  • [cyan]my brother was arrested by police[/cyan]")
    console.print("  • (press Enter to exit)\n")

    while True:
        try:
            query = input("Legal Query > ").strip()
            if not query:
                break
            response = process_query(query)
            render_response(response)
            console.print("-" * 60)
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
