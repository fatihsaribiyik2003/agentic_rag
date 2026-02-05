from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import sys

# Add the current directory to sys.path to ensure we can import the module smoothly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from agentic_rag
# Note: agentic_rag.py must have setup_vectorstore and app defined/accessible
from agentic_rag import setup_vectorstore, app as rag_app

app = FastAPI(title="Agentic RAG API", version="1.0.0")

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    success: bool
    message: str

@app.on_event("startup")
async def startup_event():
    print("Initializing Vector Store...")
    # This assumes the ./database folder exists and has PDFs.
    # We call the setup function from agentic_rag.py
    setup_vectorstore("./database")
    print("Vector Store Initialized.")

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        inputs = {"question": request.question}
        
        # Invoke the LangGraph app
        # The graph returns the final state. We expect 'generation' key in it.
        final_result = rag_app.invoke(inputs)
        
        if "generation" in final_result:
            return AnswerResponse(
                answer=final_result["generation"],
                success=True,
                message="Answer found in the documents."
            )
        else:
            return AnswerResponse(
                answer="I could not find an answer to your question in the provided documents.",
                success=False,
                message="No relevant documents found in the database."
            )
            
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
