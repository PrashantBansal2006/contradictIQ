"""
smoke.py — End-to-end smoke test script for ContradictIQ Phase 3.

Runs the canonical flow:
register -> create investigation -> upload CSV + PDF -> claims -> verify -> findings visible -> ledger valid.
Also tests tamper-evidence detection on the ledger.
"""
import asyncio
from datetime import datetime, timezone
import io
import json
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from httpx import ASGITransport, AsyncClient
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import select, update

from app.db import Base, engine, AsyncSessionLocal
from app.main import app
from app.models.models import LedgerEvent


def generate_test_pdf() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Acme Financial Results FY24 (Rs. in crore)", styles["Heading1"]),
    ]
    data = [
        ["Particulars", "FY24", "FY23"],
        ["Revenue from operations", "3,400", "2,977"],
        ["Operating expenses", "2,950", "2,587"],
        ["Operating profit", "450", "390"],
        ["Net profit", "350", "280"],
    ]
    t = Table(data, colWidths=[200, 80, 80])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def generate_test_csv() -> bytes:
    content = "metric,value,period\nrevenue,34000000000,FY2024\nnet_income,3500000000,FY2024\n"
    return content.encode("utf-8")


async def run_smoke_test():
    print("==================================================")
    print("ContradictIQ — Phase 3 End-to-End Smoke Test")
    print("==================================================")

    # 1. Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        ts = int(time.time() * 1000)
        email = f"analyst_{ts}@contradictiq.test"

        # 2. Register User (Task 3.2)
        print(f"[1/7] Registering user: {email}...")
        reg_resp = await client.post(
            "/api/auth/register",
            json={"email": email, "password": "SecurePassword123!", "name": "Senior Auditor"},
        )
        assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("      [OK] Registered successfully. JWT obtained.")

        # 3. Verify /auth/me
        me_resp = await client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200, f"/auth/me failed: {me_resp.text}"
        user_data = me_resp.json()
        assert user_data["email"] == email
        print(f"      [OK] /auth/me verified for user '{user_data['name']}'.")

        # 4. Create Investigation (Task 3.4)
        print("[2/7] Creating investigation...")
        inv_resp = await client.post(
            "/api/investigations",
            headers=headers,
            json={"title": "Acme Corp FY24 Audit", "entity_name": "Acme Corp", "description": "Verification of annual claims"},
        )
        assert inv_resp.status_code == 201, f"Create investigation failed: {inv_resp.text}"
        inv_id = inv_resp.json()["id"]
        print(f"      [OK] Investigation created with id: {inv_id}")

        # 5. Upload CSV + PDF Documents (Task 3.5)
        print("[3/7] Uploading CSV and PDF documents...")
        csv_bytes = generate_test_csv()
        csv_upload = await client.post(
            f"/api/investigations/{inv_id}/documents",
            headers=headers,
            files={"file": ("acme_data.csv", csv_bytes, "text/csv")},
        )
        assert csv_upload.status_code == 201, f"CSV upload failed: {csv_upload.text}"
        csv_doc_id = csv_upload.json()["document"]["id"]
        print(f"      [OK] CSV uploaded and ingested: {csv_doc_id}")

        pdf_bytes = generate_test_pdf()
        pdf_upload = await client.post(
            f"/api/investigations/{inv_id}/documents",
            headers=headers,
            files={"file": ("annual_report_fy24.pdf", pdf_bytes, "application/pdf")},
        )
        assert pdf_upload.status_code == 201, f"PDF upload failed: {pdf_upload.text}"
        pdf_doc_id = pdf_upload.json()["document"]["id"]
        print(f"      [OK] PDF uploaded and parsed: {pdf_doc_id}")

        # Verify documents list and facts
        doc_list = await client.get(f"/api/investigations/{inv_id}/documents", headers=headers)
        assert len(doc_list.json()) >= 2
        facts_list = await client.get(f"/api/investigations/{inv_id}/facts", headers=headers)
        assert len(facts_list.json()) >= 1
        print(f"      [OK] Extracted {len(facts_list.json())} candidate facts.")

        # 6. Create Claim & Versions (Task 3.7)
        print("[4/7] Creating financial claim...")
        claim_resp = await client.post(
            f"/api/investigations/{inv_id}/claims",
            headers=headers,
            json={
                "text": "Revenue for FY24 was ₹3,400 crore",
                "metric": "revenue",
                "claim_type": "value",
                "value_raw": "₹3,400 crore",
                "value": 3400.0,
                "scale": "crore",
                "currency": "INR",
                "period": {"kind": "FY", "fy": 2024},
            },
        )
        assert claim_resp.status_code == 201, f"Claim creation failed: {claim_resp.text}"
        claim_id = claim_resp.json()["id"]
        print(f"      [OK] Claim created with id: {claim_id}")

        # 7. Verify Claim (Task 3.8)
        print("[5/7] Running verification engine on claim...")
        verify_resp = await client.post(f"/api/claims/{claim_id}/verify", headers=headers)
        assert verify_resp.status_code == 200, f"Verification failed: {verify_resp.text}"
        finding = verify_resp.json()
        assert finding["verdict"] == "Consistent"
        assert finding["conclusion_strength"] == "Confirmed"
        assert len(finding["evidence_links"]) >= 1
        finding_id = finding["finding_id"]
        print(f"      [OK] Finding generated: Verdict={finding['verdict']} ({finding['conclusion_strength']})")
        print(f"      [OK] Calculation trace: {finding['calculation']['formula_id']}")

        # 8. Check Finding retrieval & Dashboard (Task 3.10)
        print("[6/7] Inspecting finding detail and dashboard...")
        f_resp = await client.get(f"/api/findings/{finding_id}", headers=headers)
        assert f_resp.status_code == 200
        dash_resp = await client.get(f"/api/investigations/{inv_id}/dashboard", headers=headers)
        assert dash_resp.status_code == 200
        dash = dash_resp.json()
        assert dash["counts"]["documents"] >= 2
        assert dash["counts"]["claims"] >= 1
        assert dash["counts"]["findings"] >= 1
        print("      [OK] Dashboard aggregations and queues validated.")

        # 9. Verify Hash-chained Ledger & Tamper Detection (Task 3.9)
        print("[7/7] Verifying ledger cryptographic chain & tamper detection...")
        ledger_verify = await client.get(f"/api/investigations/{inv_id}/ledger/verify", headers=headers)
        assert ledger_verify.status_code == 200
        lv_data = ledger_verify.json()
        assert lv_data["valid"] is True
        assert lv_data["head_hash"] is not None
        assert lv_data["events_count"] >= 4
        print(f"      [OK] Ledger chain verified: valid=True, head_hash={lv_data['head_hash'][:16]}..., events={lv_data['events_count']}")

        # Tamper test
        print("      Testing tamper detection: modifying one ledger row payload in DB...")
        async with AsyncSessionLocal() as db_session:
            ev_res = await db_session.execute(
                select(LedgerEvent).where(LedgerEvent.investigation_id == inv_id).limit(1)
            )
            tampered_ev = ev_res.scalar_one()
            tampered_ev.payload_json = json.dumps({"tampered": True})
            await db_session.commit()

        tampered_verify = await client.get(f"/api/investigations/{inv_id}/ledger/verify", headers=headers)
        tv_data = tampered_verify.json()
        assert tv_data["valid"] is False, "Ledger verification should have caught DB tampering!"
        print(f"      [OK] Tamper detected successfully! (tampered_event_id={tv_data['tampered_event_id']})")

    print("==================================================")
    print("ALL PHASE 3 TASKS & CHECKPOINTS PASSED CLEANLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
