import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# DİKKAT: OPENAI_API_KEY environment variable'ı tanımlı olmalı!
if "OPENAI_API_KEY" not in os.environ:
    print("UYARI: OPENAI_API_KEY bulunamadı. Lütfen environment variable olarak ekleyin.")
    # Örnek kullanım için dummy bir key set edebilirsiniz (ama çalışmaz)
    # os.environ["OPENAI_API_KEY"] = "sk-..."

class State(TypedDict):
    # Mesajlar listesine yeni mesajlar eklenerek ilerler (add_messages reducer'ı sayesinde)
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = ChatOpenAI(model="gpt-3.5-turbo")

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            print("Asistan:", value["messages"][-1].content)

def main():
    print("Chatbot Başlatıldı! (Çıkmak için 'q', 'quit' veya 'exit' yazın)")
    while True:
        try:
            user_input = input("Siz: ")
            if user_input.lower() in ["q", "quit", "exit"]:
                print("Güle güle!")
                break
            
            stream_graph_updates(user_input)
        except Exception as e:
            print(f"Hata: {e}")
            break

if __name__ == "__main__":
    main()
