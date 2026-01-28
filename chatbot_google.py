import os
from dotenv import load_dotenv

load_dotenv()
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

# DİKKAT: GOOGLE_API_KEY environment variable'ı tanımlı olmalı!
if "GOOGLE_API_KEY" not in os.environ:
    print("UYARI: GOOGLE_API_KEY bulunamadı. Lütfen environment variable olarak ekleyin.")

class State(TypedDict):
    # Mesajlar listesine yeni mesajlar eklenerek ilerler
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# Google Gemini modelini kullanıyoruz
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            print("Gemini:", value["messages"][-1].content)

def main():
    print("Google Gemini Chatbot Başlatıldı! (Çıkmak için 'q', 'quit' veya 'exit' yazın)")
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
