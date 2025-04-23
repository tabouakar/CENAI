import chromadb

client = chromadb.HttpClient("https://cenai.cse.uconn.edu/chroma/")

collection = client.get_collection(name="ethics")

print(collection.peek())
