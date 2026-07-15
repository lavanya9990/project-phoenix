from langgraph.graph import END, START, StateGraph
from app.agents import analyst, fact_checker, planner, researcher, writer
from app.graph.state import ResearchState
from app.schemas import Analysis, FactCheck, PlanItem, Source

def planner_node(state: ResearchState) -> dict:
    plan = planner.run(state["topic"], state["research_depth"])
    return {"plan": [x.model_dump() for x in plan.questions], "research_questions": [x.question for x in plan.questions], "current_step": "planner"}

def researcher_node(state: ResearchState) -> dict:
    sources, findings = researcher.run([PlanItem.model_validate(x) for x in state["plan"]], state["research_depth"])
    return {"sources": [x.model_dump() for x in sources], "findings": [x.model_dump() for x in findings], "current_step": "researcher"}

def analyst_node(state: ResearchState) -> dict:
    result = analyst.run(state["topic"], [Source.model_validate(x) for x in state["sources"]])
    return {"analysis": result.model_dump(), "current_step": "analyst"}

def fact_checker_node(state: ResearchState) -> dict:
    result = fact_checker.run(Analysis.model_validate(state["analysis"]), [Source.model_validate(x) for x in state["sources"]])
    return {"fact_check_results": result.model_dump(), "current_step": "fact_checker"}

def writer_node(state: ResearchState) -> dict:
    result = writer.run(state["topic"], Analysis.model_validate(state["analysis"]), FactCheck.model_validate(state["fact_check_results"]))
    return {"final_report": result.model_dump(), "current_step": "writer"}

def build_workflow():
    graph = StateGraph(ResearchState)
    for name, node in (("planner", planner_node), ("researcher", researcher_node), ("analyst", analyst_node), ("fact_checker", fact_checker_node), ("writer", writer_node)):
        graph.add_node(name, node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "fact_checker")
    graph.add_edge("fact_checker", "writer")
    graph.add_edge("writer", END)
    return graph.compile()

workflow = build_workflow()
