from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import LocalAIEmbeddings
import json

# Initialize the embedding model using LocalAI embeddings
embeddings = LocalAIEmbeddings(
    openai_api_base="//cenai.cse.uconn.edu/embeddings/",
    openai_api_key="not-needed",
    model="deepseek"  # This should match your model name
)

# Load your documents (using your existing ethics.json structure)
def load_documents():
    with open("ethics.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return [json.dumps(doc) for doc in data.values()]

# Split documents into chunks
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.create_documents(documents)

# Create vector store in memory using FAISS
def create_vectorstore(documents):
    return FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

# Initialize the RAG chain
def init_rag_chain(vectorstore):
    llm = ChatOpenAI(
        base_url="//cenai.cse.uconn.edu/completions/",
        api_key="not-needed",
        model_name="deepseek"  # Change this to match your model name
    )
    
    qa_template = """Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know. Don't try to make up an answer.
    
    Context: {context}
    
    Question: {question}
    
    Answer: """
    
    QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["context", "question"])
    
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT}
    )

# Main function to test the RAG system
def main():
    print("Loading documents...")
    raw_docs = load_documents()
    print(f"Loaded {len(raw_docs)} documents")
    
    print("Splitting documents...")
    split_docs = split_documents(raw_docs)
    print(f"Split into {len(split_docs)} chunks")
    
    print("Creating vector store...")
    vectorstore = create_vectorstore(split_docs)
    print("Vector store created")
    
    print("Initializing RAG chain...")
    qa_chain = init_rag_chain(vectorstore)
    print("RAG chain initialized")
    
    # Test the chain
    chat_history = []
    while True:
        question = input("Ask a question (or type 'quit' to exit): ")
        if question.lower() == 'quit':
            break
            
        print("Processing question...")
        result = qa_chain({"question": question, "chat_history": chat_history})
        print("\nAnswer:", result["answer"])
        print("\nSources:")
        for doc in result["source_documents"]:
            print("-", doc.page_content[:200], "...\n")
            
        chat_history.append((question, result["answer"]))

if __name__ == "__main__":
    main()

# OPEN AI Version Below

# from langchain_openai import ChatOpenAI
# from langchain_openai import OpenAIEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains import ConversationalRetrievalChain
# from langchain.prompts import PromptTemplate
# from langchain.vectorstores.faiss import FAISS  # In-memory vector store
# import json

# # Initialize the embedding model
# embeddings = OpenAIEmbeddings(
#     base_url="//cenai.cse.uconn.edu/embeddings/",
#     api_key="not-needed"
# )

# # Load your documents (using your existing ethics.json structure)
# def load_documents():
#     with open("ethics.json", "r", encoding="utf-8") as file:
#         data = json.load(file)
#     return [json.dumps(doc) for doc in data.values()]

# # Split documents into chunks
# def split_documents(documents):
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200,
#         length_function=len
#     )
#     return text_splitter.create_documents(documents)

# # Create vector store in memory using FAISS
# def create_vectorstore(documents):
#     return FAISS.from_documents(
#         documents=documents,
#         embedding=embeddings
#     )

# # Initialize the RAG chain
# def init_rag_chain(vectorstore):
#     llm = ChatOpenAI(
#         base_url="//cenai.cse.uconn.edu/completions/",
#         api_key="not-needed",
#         model_name="gpt-4-turbo-preview"
#     )
    
#     qa_template = """Use the following pieces of context to answer the question at the end.
#     If you don't know the answer, just say that you don't know. Don't try to make up an answer.
    
#     Context: {context}
    
#     Question: {question}
    
#     Answer: """
    
#     QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["context", "question"])
    
#     return ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
#         return_source_documents=True,
#         combine_docs_chain_kwargs={"prompt": QA_PROMPT}
#     )

# # Main function to test the RAG system
# def main():
#     # Load and process documents
#     raw_docs = load_documents()
#     split_docs = split_documents(raw_docs)
#     vectorstore = create_vectorstore(split_docs)
    
#     # Initialize the chain
#     qa_chain = init_rag_chain(vectorstore)
    
#     # Test the chain
#     chat_history = []
#     while True:
#         question = input("Ask a question (or type 'quit' to exit): ")
#         if question.lower() == 'quit':
#             break
            
#         result = qa_chain({"question": question, "chat_history": chat_history})
#         print("\nAnswer:", result["answer"])
#         print("\nSources:")
#         for doc in result["source_documents"]:
#             print("-", doc.page_content[:200], "...\n")
            
#         chat_history.append((question, result["answer"]))

# if __name__ == "__main__":
#     main()