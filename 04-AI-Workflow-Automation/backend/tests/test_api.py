def test_health(client): assert client.get("/health").json()["status"]=="ok"
def test_invalid(client): assert client.post("/api/leads",json={}).status_code==422
def test_crud_and_stats(client,payload):
    created=client.post("/api/leads",json=payload); assert created.status_code==201
    lead=created.json(); assert lead["lead_status"] in ["Hot","Warm","Cold"]; assert lead["workflow_status"]=="skipped"
    assert len(client.get("/api/leads").json())==1
    assert client.patch(f'/api/leads/{lead["id"]}',json={"follow_up_status":"completed"}).json()["follow_up_status"]=="completed"
    assert client.get("/api/dashboard/stats").json()["total_leads"]==1
    assert client.delete(f'/api/leads/{lead["id"]}').status_code==204
def test_ai_validation():
    from pydantic import ValidationError
    from app.schemas import AIAnalysis
    try: AIAnalysis(summary="x",detected_service="x",business_need="x",urgency="x",budget_category="x",lead_score=101,lead_status="Maybe",recommended_action="x",personalized_reply="x")
    except ValidationError: return
    assert False

def test_n8n_success(monkeypatch, client, payload):
    async def success(data, settings): return "completed", {"success": True}
    monkeypatch.setattr("app.services.lead_service.trigger_workflow", success)
    result=client.post("/api/leads",json=payload).json()
    assert result["workflow_status"]=="completed"

def test_n8n_failure(monkeypatch, client, payload):
    async def failure(data, settings): raise RuntimeError("Workflow failed: unavailable")
    monkeypatch.setattr("app.services.lead_service.trigger_workflow", failure)
    result=client.post("/api/leads",json=payload).json()
    assert result["workflow_status"]=="failed"
    assert result["ai_summary"]
