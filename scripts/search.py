import sys

from app.vectorstore import search

question = " ".join(sys.argv[1:]) or "Chi può autorizzare lo sbarco dei passeggeri?"
print(f"Domanda: {question}\n")
for rank, hit in enumerate(search(question), start=1):
    preview = hit["text"].replace("\n", " | ")[:140]
    print(f"{rank}. [{hit['source']} p.{hit['page']}] distanza {hit['distance']:.3f}\n   {preview}...\n")
