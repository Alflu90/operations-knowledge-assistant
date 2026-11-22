"""Valuta il recupero (retrieval) su un piccolo set di domande, senza usare il modello linguistico."""
import json
from pathlib import Path

from app.vectorstore import search

KS = (1, 3, 5)
data = json.loads(Path("data/eval_questions.json").read_text(encoding="utf-8"))

print("=== Domande con risposta nei documenti ===")
hits_at = {k: 0 for k in KS}
best_distances = []
for item in data["in_domain"]:
    hits = search(item["q"], k=max(KS))
    needle = item["must_contain"].lower()
    rank = next((i for i, h in enumerate(hits, start=1) if needle in h["text"].lower()), None)
    for k in KS:
        if rank is not None and rank <= k:
            hits_at[k] += 1
    best_distances.append(hits[0]["distance"])
    status = f"trovato al posto {rank}" if rank else "NON TROVATO"
    print(f"- {status:<18} dist1={hits[0]['distance']:.3f}  {item['q']}")

total = len(data["in_domain"])
print("\nRecupero del chunk giusto:")
for k in KS:
    print(f"  entro i primi {k}: {hits_at[k]}/{total} ({100 * hits_at[k] / total:.0f}%)")

print("\n=== Domande fuori argomento ===")
off_distances = []
for item in data["out_of_domain"]:
    hits = search(item["q"], k=1)
    off_distances.append(hits[0]["distance"])
    print(f"- dist1={hits[0]['distance']:.3f}  {item['q']}")

print("\n=== Distanza del primo risultato ===")
print(f"  con risposta:  da {min(best_distances):.3f} a {max(best_distances):.3f}")
print(f"  fuori argomento: da {min(off_distances):.3f} a {max(off_distances):.3f}")
if max(best_distances) < min(off_distances):
    print("  I due gruppi sono separati: una soglia tra questi valori distingue i casi.")
else:
    print("  I due gruppi si sovrappongono: la sola distanza non basta come soglia.")