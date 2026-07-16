import httpx

from app.config import Settings


async def trigger_workflow(payload: dict, settings: Settings):
    if not settings.n8n_webhook_url:
        return "skipped", {
            "message": "N8N_WEBHOOK_URL is not configured; demo mode is active."
        }

    try:
        async with httpx.AsyncClient(
            timeout=settings.workflow_timeout_seconds
        ) as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json=payload,
                headers={
                    "X-Webhook-Secret": settings.n8n_webhook_secret
                }
                if settings.n8n_webhook_secret
                else {},
            )

            response.raise_for_status()

        return "completed", response.json()

    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError(f"Workflow failed: {exc}") from exc