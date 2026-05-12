# PubMed pipeline: nowotwory narządu rodnego, jakość życia i konstrukty psychologiczne

Pipeline do zbudowania bazy publikacji PubMed dla tematu:

> Optymizm, akceptacja i przystosowanie psychiczne do choroby a jakość życia kobiet leczonych z powodu nowotworu narządu rodnego

## Co robi pipeline

- używa wyłącznie oficjalnego PubMed / NCBI E-utilities API;
- nie używa Google, Bing ani web search;
- nie scrapuje HTML;
- wykonuje 7 zapytań Boolean zapisanych w `config/pubmed_queries_gynecologic_qol.json`;
- pobiera listy PMID przez `esearch.fcgi`;
- scala PMID ze wszystkich zapytań;
- deduplikuje po PMID;
- pobiera metadane przez `efetch.fcgi`;
- zapisuje CSV, JSONL, raw XML/JSON i log Markdown.

## Uruchomienie lokalnie albo w Codex Cloud

```bash
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

Opcjonalnie z kluczem NCBI API:

```bash
export NCBI_API_KEY="TWÓJ_KLUCZ"
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

## Najważniejsze pliki wynikowe

Po uruchomieniu powstaną m.in.:

```text
pubmed_output_gyne_qol/data/processed/pubmed_candidates_YYYY-MM-DD.csv
pubmed_output_gyne_qol/data/processed/pubmed_candidates_YYYY-MM-DD.jsonl
pubmed_output_gyne_qol/data/processed/query_pmids_long_YYYY-MM-DD.csv
pubmed_output_gyne_qol/data/processed/queries_YYYY-MM-DD.csv
pubmed_output_gyne_qol/data/processed/deduplication_summary_YYYY-MM-DD.csv
pubmed_output_gyne_qol/data/raw/esearch/*.json
pubmed_output_gyne_qol/data/raw/efetch_batches/*.xml
pubmed_output_gyne_qol/logs/pubmed_search_log_YYYY-MM-DD.md
```

## Prompt do Codex Cloud

```text
Uruchom pipeline PubMed z tego repozytorium.

Cel:
zbudować bazę publikacji dla tematu:
„Optymizm, akceptacja i przystosowanie psychiczne do choroby a jakość życia kobiet leczonych z powodu nowotworu narządu rodnego”.

Zasady:
- używaj wyłącznie PubMed / NCBI E-utilities API;
- nie używaj Google, Bing ani ogólnego web search;
- nie scrapuj HTML;
- użyj 7 zapytań Boolean zapisanych w config/pubmed_queries_gynecologic_qol.json;
- uruchom scripts/pubmed_gynecologic_qol_search.py;
- zachowaj konserwatywne pauzy między requestami;
- jeśli dostępna jest zmienna NCBI_API_KEY, użyj jej;
- jeśli nie, działaj bez klucza.

Po zakończeniu:
1. podaj liczbę rekordów per query,
2. podaj liczbę PMID przed deduplikacją,
3. podaj liczbę unikalnych PMID po deduplikacji,
4. wskaż plik CSV z kandydatami,
5. wskaż log Markdown,
6. jeżeli pliki wynikowe nie są w repo, utwórz commit albo PR z katalogiem wynikowym.
```

## Uwaga

W środowisku ChatGPT nie udało się pobrać rekordów z NCBI z powodu błędu DNS dla `eutils.ncbi.nlm.nih.gov`. Ten pipeline jest przeznaczony do uruchomienia lokalnie, w Codex app/CLI albo w Codex Cloud z włączonym dostępem do internetu dla domen NCBI.
