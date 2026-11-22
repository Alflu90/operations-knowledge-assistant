-- name: riepilogo_domande
SELECT COUNT(*) AS domande,
       SUM(answered) AS con_risposta,
       ROUND(100.0 * SUM(answered) / COUNT(*), 1) AS perc_con_risposta,
       ROUND(AVG(latency_ms)) AS latenza_media_ms
FROM query_log;

-- name: documenti_piu_recuperati
SELECT d.filename, COUNT(*) AS volte_recuperato
FROM query_sources qs
JOIN chunks c ON c.id = qs.chunk_id
JOIN documents d ON d.id = c.document_id
GROUP BY d.filename
ORDER BY volte_recuperato DESC;

-- name: chunk_mai_recuperati
SELECT d.filename, c.page, c.chunk_index, SUBSTR(REPLACE(c.text, CHAR(10), ' '), 1, 60) AS inizio
FROM chunks c
JOIN documents d ON d.id = c.document_id
LEFT JOIN query_sources qs ON qs.chunk_id = c.id
WHERE qs.chunk_id IS NULL
ORDER BY d.filename, c.chunk_index;

-- name: distanza_media_per_esito
SELECT answered, COUNT(*) AS domande, ROUND(AVG(best_distance), 3) AS distanza_media
FROM query_log
GROUP BY answered;

-- name: domande_senza_risposta
SELECT asked_at, question, ROUND(best_distance, 3) AS miglior_distanza
FROM query_log
WHERE answered = 0
ORDER BY asked_at DESC;
