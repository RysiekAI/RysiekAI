#!/usr/bin/env python3
"""PubMed / NCBI E-utilities pipeline.

Topic:
Optymizm, akceptacja i przystosowanie psychiczne do choroby a jakość życia
kobiet leczonych z powodu nowotworu narządu rodnego.

Uses only official NCBI E-utilities:
- esearch.fcgi for PMID retrieval
- efetch.fcgi for metadata retrieval

No Google. No HTML scraping.
Optional NCBI API key: environment variable NCBI_API_KEY.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_NAME = "codex_pubmed_gyne_qol_pipeline"
DEFAULT_DELAY = 0.60
DEFAULT_ID_BATCH_SIZE = 10000
DEFAULT_FETCH_BATCH_SIZE = 200

CSV_FIELDS = [
    "record_id", "pmid", "doi", "title", "authors", "year", "journal",
    "journal_iso", "publication_date", "article_language", "publication_type",
    "mesh_terms", "keywords", "abstract", "pubmed_url", "query_ids",
    "query_labels", "search_date", "dedup_status", "screening_title_abstract",
    "exclusion_reason", "notes",
]


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def elem_text(elem: Optional[ET.Element]) -> str:
    if elem is None:
        return ""
    return clean_text("".join(elem.itertext()))


def first_text(root: ET.Element, path: str) -> str:
    return clean_text(root.findtext(path, default=""))


def load_queries(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    queries = data.get("queries", [])
    if not queries:
        raise ValueError(f"No queries found in {path}")
    return queries


def request_eutils(endpoint: str, params: Dict[str, str], *, method: str = "GET", delay: float = DEFAULT_DELAY, retries: int = 4) -> bytes:
    full_params = dict(params)
    full_params["tool"] = TOOL_NAME
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        full_params["api_key"] = api_key

    encoded = urllib.parse.urlencode(full_params).encode("utf-8")
    url = f"{EUTILS_BASE}/{endpoint}"
    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            if method.upper() == "POST":
                req = urllib.request.Request(url, data=encoded, method="POST")
            else:
                req = urllib.request.Request(url + "?" + encoded.decode("utf-8"), method="GET")
            req.add_header("User-Agent", f"{TOOL_NAME}/1.0")
            with urllib.request.urlopen(req, timeout=90) as response:
                body = response.read()
            time.sleep(delay)
            return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(delay * (2 ** attempt))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay * (2 ** attempt))
                continue
            raise

    raise RuntimeError(f"E-utilities request failed: {last_error}")


def parse_pub_date(pubmed_article: ET.Element) -> tuple[str, str]:
    article_date = pubmed_article.find(".//ArticleDate")
    if article_date is not None:
        y = article_date.findtext("Year", default="")
        m = article_date.findtext("Month", default="")
        d = article_date.findtext("Day", default="")
        if y:
            return y, "-".join(x for x in [y, m.zfill(2) if m else "", d.zfill(2) if d else ""] if x)

    pub_date = pubmed_article.find(".//Journal/JournalIssue/PubDate")
    if pub_date is not None:
        y = pub_date.findtext("Year", default="")
        medline_date = pub_date.findtext("MedlineDate", default="")
        if y:
            m = pub_date.findtext("Month", default="")
            d = pub_date.findtext("Day", default="")
            return y, " ".join(x for x in [y, m, d] if x)
        if medline_date:
            match = re.search(r"(19|20)\d{2}", medline_date)
            return (match.group(0) if match else ""), medline_date

    return "", ""


def parse_record(pubmed_article: ET.Element, pmid_to_sources: Dict[str, List[dict]], search_date: str) -> dict:
    medline = pubmed_article.find("MedlineCitation")
    article = pubmed_article.find(".//Article")
    if medline is None or article is None:
        return {}

    pmid = first_text(medline, "PMID")
    title = elem_text(article.find("ArticleTitle"))
    year, publication_date = parse_pub_date(pubmed_article)

    authors = []
    for author in article.findall(".//AuthorList/Author"):
        collective = first_text(author, "CollectiveName")
        if collective:
            authors.append(collective)
            continue
        fore = first_text(author, "ForeName")
        last = first_text(author, "LastName")
        name = clean_text(f"{fore} {last}")
        if name:
            authors.append(name)

    abstract_parts = []
    for ab in article.findall(".//Abstract/AbstractText"):
        label = ab.attrib.get("Label") or ab.attrib.get("NlmCategory") or ""
        text = elem_text(ab)
        if text:
            abstract_parts.append(f"{label}: {text}" if label else text)

    doi = ""
    for article_id in pubmed_article.findall(".//ArticleIdList/ArticleId"):
        if article_id.attrib.get("IdType", "").lower() == "doi":
            doi = elem_text(article_id)
            break

    publication_types = [elem_text(x) for x in article.findall(".//PublicationTypeList/PublicationType") if elem_text(x)]
    mesh_terms = []
    for heading in medline.findall(".//MeshHeadingList/MeshHeading"):
        descriptor = elem_text(heading.find("DescriptorName"))
        qualifiers = [elem_text(q) for q in heading.findall("QualifierName") if elem_text(q)]
        if descriptor:
            mesh_terms.append(descriptor + (" / " + ", ".join(qualifiers) if qualifiers else ""))
    keywords = [elem_text(x) for x in medline.findall(".//KeywordList/Keyword") if elem_text(x)]
    sources = pmid_to_sources.get(pmid, [])

    return {
        "record_id": f"PMID_{pmid}",
        "pmid": pmid,
        "doi": doi,
        "title": title,
        "authors": "; ".join(authors),
        "year": year,
        "journal": first_text(article, "Journal/Title"),
        "journal_iso": first_text(article, "Journal/ISOAbbreviation"),
        "publication_date": publication_date,
        "article_language": "; ".join(clean_text(x.text) for x in article.findall("Language") if x.text),
        "publication_type": "; ".join(publication_types),
        "mesh_terms": "; ".join(mesh_terms),
        "keywords": "; ".join(keywords),
        "abstract": " ".join(abstract_parts),
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        "query_ids": ";".join(sorted({s["query_id"] for s in sources})),
        "query_labels": "; ".join(f"{s['query_id']}: {s['label']}" for s in sources),
        "search_date": search_date,
        "dedup_status": "unique_by_pmid",
        "screening_title_abstract": "",
        "exclusion_reason": "",
        "notes": "",
    }


def batched(items: List[str], size: int) -> Iterable[List[str]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def write_csv(path: Path, rows: List[dict], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> int:
    base_dir = Path(__file__).resolve().parents[1]
    query_file = Path(args.query_file).expanduser()
    if not query_file.is_absolute():
        query_file = base_dir / query_file
    queries = load_queries(query_file)

    search_date = date.today().isoformat()
    out = Path(args.out).expanduser().resolve()
    raw_esearch = out / "data" / "raw" / "esearch"
    raw_efetch = out / "data" / "raw" / "efetch_batches"
    processed = out / "data" / "processed"
    logs = out / "logs"
    for d in [raw_esearch, raw_efetch, processed, logs]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Output: {out}")
    print(f"Query file: {query_file}")
    print(f"NCBI_API_KEY present: {'yes' if os.getenv('NCBI_API_KEY') else 'no'}")
    print(f"Delay: {args.delay:.2f}s")

    query_rows = []
    query_to_pmids: Dict[str, List[str]] = {}
    pmid_to_sources: Dict[str, List[dict]] = defaultdict(list)
    technical_requests = 0

    for q in queries:
        qid, label, query = q["query_id"], q["label"], q["query"]
        print(f"\n[{qid}] {label}")
        count_body = request_eutils("esearch.fcgi", {"db": "pubmed", "term": query, "retmode": "json", "retmax": "0"}, delay=args.delay)
        technical_requests += 1
        (raw_esearch / f"{qid}_count.json").write_bytes(count_body)
        count_data = json.loads(count_body.decode("utf-8"))
        count = int(count_data["esearchresult"].get("count", 0))
        warnings = count_data["esearchresult"].get("warninglist", {})
        print(f"  Count: {count}")

        all_ids: List[str] = []
        for retstart in range(0, count, args.id_batch_size):
            print(f"  PMID batch retstart={retstart}")
            ids_body = request_eutils(
                "esearch.fcgi",
                {"db": "pubmed", "term": query, "retmode": "json", "retstart": str(retstart), "retmax": str(args.id_batch_size)},
                delay=args.delay,
            )
            technical_requests += 1
            (raw_esearch / f"{qid}_ids_retstart_{retstart}.json").write_bytes(ids_body)
            ids_data = json.loads(ids_body.decode("utf-8"))
            all_ids.extend(ids_data["esearchresult"].get("idlist", []))

        seen = set()
        unique_for_query = []
        for pmid in all_ids:
            if pmid not in seen:
                seen.add(pmid)
                unique_for_query.append(pmid)
                pmid_to_sources[pmid].append({"query_id": qid, "label": label})

        query_to_pmids[qid] = unique_for_query
        query_rows.append({
            "query_id": qid,
            "label": label,
            "purpose": q.get("purpose", ""),
            "query": query,
            "count_reported_by_pubmed": count,
            "pmids_retrieved_for_query": len(unique_for_query),
            "warnings": json.dumps(warnings, ensure_ascii=False),
        })

    all_unique_pmids = sorted(pmid_to_sources.keys(), key=lambda x: int(x) if x.isdigit() else x)
    total_query_hits = sum(len(v) for v in query_to_pmids.values())
    print(f"\nPMID before deduplication: {total_query_hits}")
    print(f"Unique PMID after deduplication: {len(all_unique_pmids)}")

    qpmid_rows = []
    for q in queries:
        for pmid in query_to_pmids[q["query_id"]]:
            qpmid_rows.append({"query_id": q["query_id"], "query_label": q["label"], "pmid": pmid})
    write_csv(processed / f"query_pmids_long_{search_date}.csv", qpmid_rows, ["query_id", "query_label", "pmid"])
    write_csv(processed / f"queries_{search_date}.csv", query_rows, ["query_id", "label", "purpose", "query", "count_reported_by_pubmed", "pmids_retrieved_for_query", "warnings"])
    write_csv(processed / f"deduplication_summary_{search_date}.csv", [
        {"metric": "total_query_level_pmids_before_deduplication", "value": total_query_hits},
        {"metric": "unique_pmids_after_deduplication", "value": len(all_unique_pmids)},
        {"metric": "duplicate_query_hits_removed", "value": total_query_hits - len(all_unique_pmids)},
    ], ["metric", "value"])

    records = []
    batch_rows = []
    for batch_no, ids in enumerate(batched(all_unique_pmids, args.fetch_batch_size), start=1):
        print(f"EFetch batch {batch_no}: {len(ids)} PMID")
        xml_body = request_eutils(
            "efetch.fcgi",
            {"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "rettype": "abstract"},
            method="POST",
            delay=args.delay,
        )
        technical_requests += 1
        xml_path = raw_efetch / f"efetch_batch_{batch_no:04d}.xml"
        xml_path.write_bytes(xml_body)
        batch_rows.append({"batch_number": batch_no, "record_count_requested": len(ids), "file": str(xml_path)})
        root = ET.fromstring(xml_body)
        for article in root.findall("PubmedArticle"):
            rec = parse_record(article, pmid_to_sources, search_date)
            if rec:
                records.append(rec)

    csv_path = processed / f"pubmed_candidates_{search_date}.csv"
    jsonl_path = processed / f"pubmed_candidates_{search_date}.jsonl"
    write_csv(csv_path, records, CSV_FIELDS)
    with jsonl_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_csv(processed / f"efetch_batches_index_{search_date}.csv", batch_rows, ["batch_number", "record_count_requested", "file"])

    log_path = logs / f"pubmed_search_log_{search_date}.md"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"# PubMed search log — {search_date}\n\n")
        f.write("## Topic\n\nOptymizm, akceptacja i przystosowanie psychiczne do choroby a jakość życia kobiet leczonych z powodu nowotworu narządu rodnego.\n\n")
        f.write("## Method\n\n- Source: PubMed via official NCBI E-utilities API.\n- No Google. No HTML scraping.\n- Endpoints: `esearch.fcgi`, `efetch.fcgi`.\n")
        f.write(f"- NCBI_API_KEY present: {'yes' if os.getenv('NCBI_API_KEY') else 'no'}.\n")
        f.write(f"- Delay between requests: {args.delay:.2f}s.\n")
        f.write(f"- Technical API requests: {technical_requests}.\n\n")
        f.write("## Query-level results\n\n| Query | Label | PubMed Count | PMID retrieved |\n|---|---|---:|---:|\n")
        for row in query_rows:
            f.write(f"| {row['query_id']} | {row['label']} | {row['count_reported_by_pubmed']} | {row['pmids_retrieved_for_query']} |\n")
        f.write("\n## Deduplication\n\n")
        f.write(f"- Total query-level PMID hits before deduplication: {total_query_hits}\n")
        f.write(f"- Unique PMID after deduplication: {len(all_unique_pmids)}\n")
        f.write(f"- Duplicate query hits removed: {total_query_hits - len(all_unique_pmids)}\n")
        f.write(f"- Parsed records saved: {len(records)}\n\n")
        f.write("## Main output files\n\n")
        f.write(f"- CSV: `{csv_path}`\n")
        f.write(f"- JSONL: `{jsonl_path}`\n")

    print("\nDone.")
    print(f"CSV: {csv_path}")
    print(f"JSONL: {jsonl_path}")
    print(f"Log: {log_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PubMed candidate database for gynecologic cancer QoL/psychological constructs.")
    parser.add_argument("--out", default="pubmed_output_gyne_qol", help="Output directory")
    parser.add_argument("--query-file", default="config/pubmed_queries_gynecologic_qol.json", help="JSON file with Boolean queries")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Delay after each request")
    parser.add_argument("--id-batch-size", type=int, default=DEFAULT_ID_BATCH_SIZE, help="ESearch PMID batch size")
    parser.add_argument("--fetch-batch-size", type=int, default=DEFAULT_FETCH_BATCH_SIZE, help="EFetch metadata batch size")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
