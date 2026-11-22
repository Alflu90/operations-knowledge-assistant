import sys

from app.rag import answer

question = " ".join(sys.argv[1:]) or "Chi può autorizzare lo sbarco dei passeggeri?"
result = answer(question)

print(f"\nDomanda: {question}\n")
print(result["answer"])
if result["sources"]:
    print("\nFonti:")
    for i, s in enumerate(result["sources"], start=1):
        print(f"  [{i}] {s['source']}, pagina {s['page']} (distanza {s['distance']:.3f})")
else:
    best = result["retrieved"][0]["distance"] if result["retrieved"] else None
    detail = f" (miglior distanza trovata: {best:.3f})" if best is not None else ""
    print(f"\nNessuna fonte utilizzata{detail}.")
