# Codex Cloud runbook — PubMed E-utilities pipeline

## Problem zaobserwowany

Pipeline nie uruchomił się poprawnie w Codex Cloud z dwóch powodów:

1. Pierwsza komenda została uruchomiona z niewłaściwego katalogu:

```bash
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

w katalogu:

```text
/workspace/RysiekAI
```

Tam nie ma ścieżki `scripts/pubmed_gynecologic_qol_search.py`, bo pipeline znajduje się głębiej:

```text
/workspace/RysiekAI/research/pubmed-gyne-qol-pipeline
```

2. Druga komenda wskazała poprawny plik, ale zakończyła się błędem proxy/tunnel:

```text
urllib.error.URLError: <urlopen error Tunnel connection failed: 403 Forbidden>
```

To oznacza, że środowisko Codex Cloud nie miało włączonego albo poprawnie dozwolonego dostępu internetowego do NCBI E-utilities.

## Poprawny katalog roboczy

W Codex Cloud ustaw:

```text
Repository: RysiekAI/RysiekAI
Branch: chrome-extension-starter
Working directory: research/pubmed-gyne-qol-pipeline
```

Wtedy komenda:

```bash
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

będzie poprawna.

Alternatywnie z katalogu root repozytorium można uruchomić:

```bash
python3 research/pubmed-gyne-qol-pipeline/scripts/pubmed_gynecologic_qol_search.py --out research/pubmed-gyne-qol-pipeline/pubmed_output_gyne_qol --query-file research/pubmed-gyne-qol-pipeline/config/pubmed_queries_gynecologic_qol.json
```

## Wymagany internet access / egress

Pipeline używa wyłącznie oficjalnego PubMed / NCBI E-utilities API.

Należy włączyć internet access dla:

```text
eutils.ncbi.nlm.nih.gov
pubmed.ncbi.nlm.nih.gov
ncbi.nlm.nih.gov
```

Minimalnie wymagany host do samego API:

```text
eutils.ncbi.nlm.nih.gov
```

Metody HTTP:

```text
GET
POST
HEAD
OPTIONS
```

Uwaga: skrypt używa `GET` dla `esearch.fcgi` oraz `POST` dla `efetch.fcgi`, aby uniknąć zbyt długich URL-i przy dużych listach PMID.

## Test diagnostyczny przed uruchomieniem pipeline'u

W Codex Cloud można najpierw uruchomić:

```bash
python3 - <<'PY'
import urllib.request
url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer&retmode=json&retmax=1'
print(urllib.request.urlopen(url, timeout=30).read()[:500].decode('utf-8'))
PY
```

Jeżeli ten test daje `403 Forbidden`, problemem jest egress/proxy, nie kod pipeline'u.

## Właściwy run

Po odblokowaniu egress:

```bash
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

Opcjonalnie z kluczem NCBI API:

```bash
export NCBI_API_KEY="TWÓJ_KLUCZ"
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol
```

## Oczekiwane pliki wynikowe

Po udanym przebiegu:

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

## Prompt do ponownego uruchomienia w Codex Cloud

```text
Pracuj w katalogu:
research/pubmed-gyne-qol-pipeline

Najpierw wykonaj diagnostykę dostępu do:
eutils.ncbi.nlm.nih.gov

Jeżeli diagnostyka przejdzie, uruchom:
python3 scripts/pubmed_gynecologic_qol_search.py --out pubmed_output_gyne_qol

Nie używaj Google, Bing, web search ani scrapingu HTML. Używaj wyłącznie PubMed / NCBI E-utilities API.

Po zakończeniu podaj:
1. liczbę rekordów per query,
2. liczbę PMID przed deduplikacją,
3. liczbę unikalnych PMID po deduplikacji,
4. ścieżkę do CSV,
5. ścieżkę do JSONL,
6. ścieżkę do logu Markdown.
```
