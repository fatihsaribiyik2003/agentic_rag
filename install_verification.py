try:
    import langgraph
    import langchain
    print("LangGraph installed successfully!")
    print(f"LangGraph version: {langgraph.__version__}")
except ImportError as e:
    print(f"Installation failed: {e}")
