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
    """
    Represents the state of our graph.
    """
    question: str
    generation: str
    documents: List[str]
    sub_questions: List[str]
    chat_history: List[str] # added chat_history

# --- Nodes ---

def decompose_query(state):
    """
    Decompose the query into sub-questions.
    """
    print("---DECOMPOSE QUERY---")
    question = state["question"]
    
    # Prompt to decompose
    prompt = PromptTemplate(
        template="""Sen karmaşık bir soruyu daha basit alt sorulara bölen akıllı bir asistansın.
        
        GEÇMİŞ KONUŞMA:
        {chat_history}
        
        GÖREVİN:
        Kullanıcının sorduğu soruyu analiz et. Eğer soru geçmiş konuşmaya atıfta bulunuyorsa (örneğin "bu ne demek", "olmadı" gibi), geçmişi kullanarak soruyu netleştir.
        Soruyu cevaplamak için gereken alt soruları listele.
        
        KURALLAR:
        1. Sadece gerekli olan soruları üret.
        2. Geçmiş konuşmayı dikkate alarak eksik bilgileri tamamla (Coreference Resolution).
        3. SORGU GENİŞLETME (ÖNEMLİ): Eğer soru bir işlemin nasıl yapılacağını soruyorsa, mutlaka 3 farklı varyasyon üret:
           a) Orijinal soru (örn: "nasıl üye olurum")
           b) Resmi/Edilgen hali (örn: "üyelik işlemleri nasıl yapılır", "üyelik başvuru süreci")
           c) Gereklilik hali (örn: "üyelik için gerekli belgeler nelerdir")
        4. CEVABI SADECE JSON FORMATINDA VER. Başka hiçbir metin ekleme.
        
        Orijinal Soru: {question}
        
        İstenen JSON Formatı:
        {{
            "sub_questions": ["Orijinal Soru?", "Resmi Soru Varyasyonu?", "Gereklilik Soru Varyasyonu?"]
        }}
        """,
        input_variables=["question", "chat_history"],
    )
    
    chain = prompt | llm | JsonOutputParser()
    try:
        # Pass chat_history from state, default to empty list if none
        history = state.get("chat_history", [])
        # Format history as a string for the prompt
        formatted_history = "\\n".join(history) if history else "Yok"
        
        response = chain.invoke({"question": question, "chat_history": formatted_history})
        sub_questions = response.get("sub_questions", [question])
    except Exception as e:
        print(f"Decomposition failed: {e}")
        sub_questions = [question]
        
    # Validation
    if not sub_questions:
        sub_questions = [question]
        
    print(f"Generated sub-questions: {sub_questions}")
    return {"sub_questions": sub_questions}

def retrieve(state):
    """
    Retrieve documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    sub_questions = state.get("sub_questions", [question])
    
    all_documents = []
    seen_content = set()
    
    for q in sub_questions:
        print(f"Searching for: {q}")
        documents = retriever.invoke(q)
        for doc in documents:
            # Simple deductive based on page content to avoid duplicates from overlapping searches
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                all_documents.append(doc)
    
    print(f"Total unique documents retrieved: {len(all_documents)}")
    return {"documents": all_documents, "question": question}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    print("---CHECK RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # Grader prompt
    prompt = PromptTemplate(
        template="""Sen bir belge değerlendiricisisin. Bir belgenin kullanıcının sorusuyla alakalı olup olmadığını kontrol ediyorsun. \n 
        İşte alınan belge: \n\n {document} \n\n
        İşte kullanıcının sorusu: {question} \n
        Eğer belge kullanıcının sorusunun HERHANGİ BİR KISMI ile ilgili anahtar kelimeler veya anlamsal içerik barındırıyorsa, onu alakalı olarak işaretle. \n
        Belgenin soruyla ilgili olup olmadığını belirtmek için 'yes' (evet) veya 'no' (hayır) şeklinde ikili bir puan ver. \n
        Puanı tek bir 'score' anahtarı içeren JSON formatında ver, başka hiçbir açıklama yapma.""",
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
        template="""Sen yardımsever, özgüvenli ve çözüm odaklı bir müşteri hizmetleri temsilcisisin.
        
        GÖREVİN:
        Aşağıdaki bilgi parçalarını kullanarak müşterinin sorusuna DOĞRUDAN ve NET bir cevap ver.
        
        KURALLAR:
        1. ASLA "Belgede yazıyor", "Bağlamda belirtilmiş", "Dokümana göre" gibi ifadeler kullanma. Sanki bu bilgileri ezbere biliyormuşsun gibi konuş.
        2. Müşteriye "SİZ" diliyle hitap et (Örn: "Yapabilirsiniz", "Edersiniz").
        3. Eğer net bir adım-adım kılavuz yoksa bile, elindeki ipuçlarını birleştirerek en mantıklı yolu tarif et. (Örn: "Sisteme giriş ekranından kayıt olabilirsiniz").
        4. Olumsuz konuşma ("Bilgi yok" deme). Onun yerine alternatif çözüm sun ("Bu konuda en doğru bilgiyi öğrenci işlerinden alabilirsiniz" de).
        5. Cevabı kısa tut (Maksimum 3-4 cümle).
        6. Sorulan sorunun dili ne ise (Türkçe, İngilizce vb.) o dilde cevap ver.
        
        Soru: {question} 
        Bilgi Parçaları: {context} 
        
        Senin Cevabın:""",
        input_variables=["question", "context"],
    )
    
    # Chain
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

# --- Conditional Edges ---

def route_query(state):
    """
    Route query to RAG or Chitchat.
    """
    print("---ROUTE QUERY---")
    question = state["question"]
    
    prompt = PromptTemplate(
        template="""Sen gelen mesajları sınıflandıran bir uzmansın.
        Gelen mesajın "TEKNİK" (SADOS, eğitim, sınav, sertifika, ödeme, giriş sorunları) mi yoksa "SOHBET" (selamlaşma, teşekkür, şikayet, sitem, rastgele konuşma) mi olduğuna karar ver.

        Mesaj: {question}

        Sadece 'RAG' (teknikse) veya 'CHITCHAT' (sohbetse) kelimesini döndür.
        """,
        input_variables=["question"],
    )
    
    chain = prompt | llm | StrOutputParser()
    decision = chain.invoke({"question": question})
    
    if "RAG" in decision:
        print("---DECISION: ROUTE TO RAG---")
        return "rag"
    else:
        print("---DECISION: ROUTE TO CHITCHAT---")
        return "chitchat"

def handle_chitchat(state):
    """
    Handle chitchat messages without retrieval.
    """
    print("---HANDLE CHITCHAT---")
    question = state["question"]
    chat_history = state.get("chat_history", [])
    formatted_history = "\\n".join(chat_history) if chat_history else "Yok"

    prompt = PromptTemplate(
        template="""Sen yardımsever bir müşteri hizmetleri asistanısın.
        Kullanıcının mesajına, geçmiş konuşmayı da dikkate alarak nazik, profesyonel6. Sorulan sorunun dili ne ise (Türkçe, İngilizce vb.) o dilde cevap ver.
        
        GEÇMİŞ KONUŞMA:
        {chat_history}
        
        Kullanıcı Mesajı: {question}
        
        Cevap:""",
        input_variables=["question", "chat_history"],
    )
    
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"question": question, "chat_history": formatted_history})
    
    return {"generation": generation}


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
workflow.add_node("decompose_query", decompose_query)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("handle_chitchat", handle_chitchat) # Added node

# Build graph
# Replace START -> decompose with Conditional Edge
workflow.add_conditional_edges(
    START,
    route_query,
    {
        "rag": "decompose_query",
        "chitchat": "handle_chitchat",
    },
)

workflow.add_edge("decompose_query", "retrieve")
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
workflow.add_edge("handle_chitchat", END) # Edge for chitchat

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
    chat_history = []
    while True:
        question = input("\nAsk a question (or 'q' to quit): ")
        if not question.strip():
            continue
            
        if question.lower() in ["q", "quit"]:
            break
            
        inputs = {"question": question, "chat_history": chat_history}
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
                answer = final_result['generation']
                print(f"\nAnswer: {answer}")
                
                # Update Chat History
                chat_history.append(f"Kullanıcı: {question}")
                chat_history.append(f"Asistan: {answer}")
                # Keep only last 10 messages to avoid huge prompts
                if len(chat_history) > 10:
                    chat_history = chat_history[-10:]
            else:
                print("\nCould not generate an answer (No relevant documents found).")
                
        except Exception as e:
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    main()
