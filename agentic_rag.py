import os
import sys
from dotenv import load_dotenv
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

# LangChain / LangGraph imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langgraph.graph import END, StateGraph, START

load_dotenv()

# --- Configuration & Setup ---
if "GOOGLE_API_KEY" not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not found.")
    sys.exit(1)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Initialize Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# --- Vector Store Setup ---
VECTORSTORE_DIR = "./chroma_db"
vectorstore = None
retriever = None

def setup_vectorstore(data_dir: str = "./database"):
    global vectorstore, retriever
    print(f"Scanning directory: {data_dir}...")
    
    if not os.path.exists(data_dir):
        print(f"Directory '{data_dir}' not found. Creating it...")
        os.makedirs(data_dir)
        print("Please put your PDF files in the 'database' folder and restart.")
        return

    # Find all PDFs
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in 'database' folder.")
        return

    all_docs = []
    for pdf_file in pdf_files:
        path = os.path.join(data_dir, pdf_file)
        print(f"Loading: {pdf_file}...")
        try:
            loader = PyPDFLoader(path)
            all_docs.extend(loader.load())
        except Exception as e:
            print(f"Failed to load {pdf_file}: {e}")

    if not all_docs:
        print("No valid documents loaded.")
        return

    # Split text
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=200
    )
    doc_splits = text_splitter.split_documents(all_docs)
    print(f"Total split chunks: {len(doc_splits)}")

    # Create Dictionary
    # Note: For production, you might want to persist this. 
    # Here we recreate it for the script run.
    print("Creating Vector Store...")
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=embeddings,
    )
    retriever = vectorstore.as_retriever()
    print("Vector Store Ready.")

# --- Graph Dictionary ---

class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    question: str
    generation: str
    documents: List[str]

# --- Nodes ---

def retrieve(state):
    """
    Retrieve documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    print("---CHECK RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # Grader prompt
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {document} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
        Provide the binary score as a JSON with a single key 'score' and no premable or explanation.""",
        input_variables=["question", "document"],
    )
    
    chain = prompt | llm | JsonOutputParser()
    
    filtered_docs = []
    for d in documents:
        score = chain.invoke({"question": question, "document": d.page_content})
        grade = score["score"]
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
            
    return {"documents": filtered_docs, "question": question}

def generate(state):
    """
    Generate answer
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    # Generation prompt
    prompt = PromptTemplate(
        template="""You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        
        Question: {question} 
        Context: {context} 
        Answer:""",
        input_variables=["question", "context"],
    )
    
    # Chain
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

# --- Conditional Edges ---

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    print("---ASSESS GRADED DOCUMENTS---")
    filtered_documents = state["documents"]
    
    if not filtered_documents:
        # We have no relevant documents, so (in a full agentic RAG) we might rewrite the query.
        # For this simple example, we will just end but returning a message.
        print("---DECISION: NO RELEVANT DOCUMENTS FOUND---")
        return "end_no_docs"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"

# --- Build Graph ---

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

# Build graph
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")

# Conditional edge
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
        "end_no_docs": END,
    },
)
workflow.add_edge("generate", END)

# Compile
app = workflow.compile()

def main():
    print("--- Agentic RAG Setup ---")
    
    try:
        # Load all files from ./database
        setup_vectorstore("./database")
        
        if vectorstore is None:
            print("Vector Store not initialized. Exiting.")
            return

    except Exception as e:
        print(f"Error setting up vector store: {e}")
        return

    print("\n--- Interaction ---")
    while True:
        question = input("\nAsk a question (or 'q' to quit): ")
        if question.lower() in ["q", "quit"]:
            break
            
        inputs = {"question": question}
        try:
            for output in app.stream(inputs):
                for key, value in output.items():
                    # print(f"Node '{key}':")
                    pass
            
            # Final generation result is usually in the last state of 'generate' node
            # But since we stream, we can just print the final result if we stored it properly
            # or we can look at the flow. Ideally, the `generate` node updates the state `generation`.
            # Let's verify what `app.invoke` returns for simplicity in printing.
            
            final_result = app.invoke(inputs)
            if "generation" in final_result:
                print(f"\nAnswer: {final_result['generation']}")
            else:
                print("\nCould not generate an answer (No relevant documents found).")
                
        except Exception as e:
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    main()
