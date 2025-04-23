import chromadb
import json
from langchain_text_splitters import CharacterTextSplitter


def add_file_to_collection(collection="default", filename = None):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    print(f'Processing {filename}')
    documents = list(data.values())

    # Split the doucments by tokens; tokens are estimated by the 
    # "tiktoken" encoder by OpenAI. 
    # Adapted from https://python.langchain.com/docs/concepts/text_splitters/
    url_metadata = []
    split_documents = []
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base", chunk_size=100, chunk_overlap=10
    )
    for doc in documents:
        if type(doc) != dict:
            texts = text_splitter.split_text(doc)
            for split_document in texts:
                split_documents.append(split_document)
                url_metadata.append({"source":"not found"})
            continue
        full_document = doc["Content"]
        url = doc["URL"]
        texts = text_splitter.split_text(full_document)
        for split_document in texts:
            split_documents.append(split_document)
            url_metadata.append({"source":url})
    
    client = chromadb.HttpClient(host="localhost", port=9000)
    collection = client.get_or_create_collection(collection)
    cur_count = collection.count()

    collection.add(
            ids=[str(x + cur_count) for x in range(len(split_documents))],
            documents=split_documents,
            metadatas=url_metadata
    )

if __name__ == "__main__":
    ethics_files = ["ethics.json",
                    "ctgov-site.json"]
    # CTGov file not formatted in the same manner.

    for file in ethics_files:
        add_file_to_collection("ethics", file)

    cisco_files = ["specific_cisco_content2.json"]
    for file in cisco_files:
        add_file_to_collection("cisco", file)
