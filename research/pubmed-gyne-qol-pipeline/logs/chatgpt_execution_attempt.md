# Próba wykonania w ChatGPT

Próba bezpośredniego wykonania zapytań przez runtime plikowy zakończyła się błędem:

```text
Failed to resolve 'eutils.ncbi.nlm.nih.gov'
```

To oznacza ograniczenie sieci/DNS w środowisku, w którym ChatGPT tworzy pliki, nie błąd zapytań PubMed.

Wykonałem przygotowanie pełnego pakietu lokalnego:

- 7 zapytań Boolean,
- skrypt ESearch + EFetch,
- pauzy między requestami,
- deduplikacja po PMID,
- eksport CSV/JSONL,
- log metodologiczny,
- surowe ESearch JSON i EFetch XML w batchach.
