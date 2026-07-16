import json
import httpx
from app.config import Settings
from app.schemas import AIAnalysis, LeadCreate
PROMPT = "Return only JSON with summary, detected_service, business_need, urgency, budget_category, lead_score 0-100, lead_status Hot/Warm/Cold, recommended_action, personalized_reply. Do not invent facts."
def demo_analysis(lead: LeadCreate) -> AIAnalysis:
    text = f"{lead.enquiry} {lead.preferred_timeline or ''}".lower(); urgent = any(x in text for x in ("urgent","within one","asap","this month")); budget = bool(lead.estimated_budget)
    score = min(100, 35 + (25 if len(lead.enquiry.split()) >= 7 else 0) + (20 if budget else 0) + (15 if urgent else 0)); status = "Hot" if score >= 75 else "Warm" if score >= 50 else "Cold"
    return AIAnalysis(summary=lead.enquiry[:240], detected_service="AI workflow automation", business_need=lead.enquiry, urgency="High" if urgent else "Normal", budget_category="Provided" if budget else "Not provided", lead_score=score, lead_status=status, recommended_action="Schedule a discovery call within 24 hours." if status == "Hot" else "Send information and arrange a follow-up.", personalized_reply=f"Hi {lead.full_name}, thank you for your enquiry. We will follow up shortly.")
async def analyze_lead(lead: LeadCreate, settings: Settings) -> AIAnalysis:
    if not settings.groq_api_key: return demo_analysis(lead)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.groq_api_key}"}, json={"model":settings.groq_model,"temperature":0.2,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":PROMPT},{"role":"user","content":lead.model_dump_json()}]}); response.raise_for_status()
        return AIAnalysis.model_validate(json.loads(response.json()["choices"][0]["message"]["content"]))
    except (httpx.HTTPError, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc: raise RuntimeError(f"AI analysis failed: {exc}") from exc
