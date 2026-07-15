export type PlanItem = { question: string; rationale: string };
export type Source = { title: string; url: string; snippet: string; research_question: string };
export type Research = { research_id: number; topic: string; status: string; research_depth: "quick" | "standard" | "deep"; plan: PlanItem[]; sources: Source[]; final_report: string; error_message?: string; created_at: string; updated_at: string };
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
async function call<T>(path: string, options?: RequestInit): Promise<T> { const response = await fetch(`${API}${path}`, options); if (!response.ok) throw new Error((await response.text()) || "Request failed"); return response.status === 204 ? (undefined as T) : response.json(); }
export const researchApi = { list: () => call<Research[]>("/api/research"), create: (topic: string, research_depth: string) => call<Research>("/api/research", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ topic, research_depth }) }), remove: (id: number) => call<void>(`/api/research/${id}`, { method: "DELETE" }) };
