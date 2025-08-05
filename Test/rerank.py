# pip install sentence-transformers sqlparse
from sentence_transformers import CrossEncoder
import numpy as np
import sqlparse

# 1. Normalização simples
def normalize_sql(q: str) -> str:
    q = sqlparse.format(q, strip_comments=True, keyword_case="upper", reindent=False)
    return " ".join(q.split())

# 2. Heurísticas rápidas (ajuste pesos como quiser)
def rule_score(sql: str, forbidden=("DELETE","UPDATE","INSERT","ALTER"), penalize_star=True):
    s = 1.0
    up = sql.upper()
    if any(f in up for f in forbidden):
        return 0.0
    if penalize_star and "SELECT *" in up:
        s -= 0.1
    return max(0.0, s)

# 3. Reranker
model = CrossEncoder("BAAI/bge-reranker-v2-m3", trust_remote_code=True)

def pick_best_query(question: str, candidates: list[str], top_k=3):
    normed = [normalize_sql(c) for c in candidates]
    pairs = [(question, q) for q in normed]
    model_scores = model.predict(pairs)  # float array
    rules = np.array([rule_score(q) for q in normed])

    final = 0.7 * model_scores + 0.3 * rules
    order = final.argsort()[::-1]

    return [{
        "rank": i+1,
        "sql": candidates[idx],
        "norm_sql": normed[idx],
        "model_score": float(model_scores[idx]),
        "rule_score": float(rules[idx]),
        "final_score": float(final[idx])
    } for i, idx in enumerate(order[:top_k])]

# ----------------- USO -----------------
question = "Quais clientes gastaram mais de R$ 5.000 em 2024?"
candidates = [
    "SELECT cliente_id, SUM(valor) AS total FROM vendas WHERE data >= '2024-01-01' GROUP BY cliente_id HAVING SUM(valor) > 5000;",
    "SELECT * FROM vendas;",
    "WITH t AS (SELECT ...) SELECT ..."
]

results = pick_best_query(question, candidates, top_k=1)
best = results[0]["sql"]
print(best)
