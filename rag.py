import sys

# Patch the standard sqlite3 module with pysqlite3 to ensure compatibility with ChromaDB, which requires SQLite version >= 3.35.0 (often not available in default Python builds) for streamlit cloud.

try:
    import pysqlite3 # type: ignore
    sys.modules["sqlite3"] = sys.modules["pysqlite3"]
except ImportError:
    pass

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

load_dotenv()

# Constants
CHUNK_SIZE = 1000
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"
COLLECTION_NAME = "real_estate"

llm = None
vector_store = None


def initialize_components():
    global llm, vector_store

    if llm is None:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.9, max_tokens=1024)

    if vector_store is None:
        ef = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"trust_remote_code": True} # To use the code which is not part of standard library
        )

        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=ef,
            persist_directory=str(VECTORSTORE_DIR)
        )

def load_url_with_headers(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36'
    }

    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        raise ValueError(f"Failed to fetch {url}. The server returned status code: {res.status_code}. This may be a broken link or the site is actively blocking automated scrapers.")
        
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Remove all script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
        
    # Extract all text, separating by newline
    text = soup.get_text(separator='\n', strip=True)

    return Document(page_content=text, metadata={"source": url})

def process_urls(urls):
    """
    This function scraps data from a url and stores it in a vector db
    :param urls: input urls
    :return:
    """
    yield "Initializing Components"
    initialize_components()

    yield "Resetting vector store...✅"
    vector_store.reset_collection()

    yield "Loading data...✅"
    data = [load_url_with_headers(url) for url in urls]

    yield "Splitting text into chunks...✅"
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=CHUNK_SIZE
    )
    docs = text_splitter.split_documents(data)
    for doc in docs:
        if "source" not in doc.metadata:
            doc.metadata["source"] = "unknown"

    yield "Add chunks to vector database...✅"
    uuids = [str(uuid4()) for _ in range(len(docs))]
    vector_store.add_documents(docs, ids=uuids)

    yield "Done adding docs to vector database...✅"

def generate_answer(query):
    if not vector_store:
        raise RuntimeError("Vector database is not initialized ")

    # Enhance query to prevent repetition and formatting issues
    enhanced_query = (
        f"{query}\n\n"
        "(Provide your explanation in exactly 2 short paragraphs (around 5 lines total). "
        "Start with a Level 3 Markdown heading (### Title). "
        "Do not repeat the question.)"
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=vector_store.as_retriever(), 
        return_source_documents=True
    )
    result = chain.invoke({"query": enhanced_query})
    answer = result.get('result', '')
    
    source_docs = result.get('source_documents', [])
    unique_sources = set([doc.metadata.get('source', '') for doc in source_docs])
    sources = ",".join([s for s in unique_sources if s])

    return answer, sources


if __name__ == "__main__":
    urls = [
        "https://www.cnbc.com/2024/12/21/how-the-federal-reserves-rate-policy-affects-mortgages.html",
        "https://www.cnbc.com/2024/12/20/why-mortgage-rates-jumped-despite-fed-interest-rate-cut.html"
    ]

    process_urls(urls)
    answer, sources = generate_answer("Tell me what was the 30 year fixed mortgage rate along with the date?")
    print(f"Answer: {answer}")
    print(f"Sources: {sources}")