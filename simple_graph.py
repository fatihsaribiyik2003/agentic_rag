from langgraph.graph import START, StateGraph
from typing import TypedDict

class State(TypedDict):
    text: str

def node_a(state: State) -> dict:
    print("---Node A---")
    return {"text": state["text"] + "a"}

def node_b(state: State) -> dict:
    print("---Node B---")
    return {"text": state["text"] + "b"}

def main():
    graph = StateGraph(State)
    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    
    graph.add_edge(START, "node_a")
    graph.add_edge("node_a", "node_b")
    
    app = graph.compile()
    
    print("Running Simple Graph...")
    result = app.invoke({"text": ""})
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
