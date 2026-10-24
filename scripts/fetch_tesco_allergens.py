#!/usr/bin/env python3
"""Build auditable Tesco allergen snapshots from current product pages.

`free` means no declaration was found in a complete online ingredient/allergen
label at the checked date. It is not a medical guarantee or certification.
Products without a complete online label remain `unknown` unless the label
explicitly declares an allergen.
"""
import argparse
import csv
import hashlib
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from lxml import html
import requests

from catalogue import ROOT, read_csv

ALLERGEN_ALIASES = {
    "celery": (r"celery", r"celeriac"),
    "cereals_containing_gluten": (
        r"gluten", r"wheat", r"spelt", r"khorasan", r"kamut", r"rye", r"barley", r"oats?"
    ),
    "crustaceans": (r"crustaceans?", r"prawns?", r"shrimps?", r"crabs?", r"lobsters?", r"crayfish", r"shellfish"),
    "eggs": (r"eggs?",),
    "fish": (r"fish", r"salmon", r"cod", r"tuna", r"anchov(?:y|ies)", r"haddock", r"sea bass"),
    "lupin": (r"lupin",),
    "milk": (r"milk", r"lactose", r"whey", r"casein"),
    "molluscs": (r"molluscs?", r"mussels?", r"oysters?", r"squid", r"scallops?", r"shellfish"),
    "mustard": (r"mustard",),
    "peanuts": (r"peanuts?", r"groundnuts?"),
    "sesame": (r"sesame",),
    "soya": (r"soya", r"soy"),
    "sulphur_dioxide_sulphites": (
        r"sulphur dioxide", r"sulpher dioxide", r"sulphites?", r"sulfites?", r"metabisulphites?"
    ),
    "tree_nuts": (
        r"nuts?", r"almonds?", r"hazelnuts?", r"walnuts?", r"cashews?", r"pecans?",
        r"brazil nuts?", r"pistachios?", r"macadamias?"
    ),
}
STATUS_ORDER = {"unknown": 0, "free": 1, "may_contain": 2, "contains": 3}
THREAD_LOCAL = threading.local()


def clean(value):
    return " ".join((value or "").split())


def clean_ingredient_section(value):
    """Remove neighbouring accordion sections accidentally captured by Tesco HTML.

    Some products have an outer ``Ingredients`` accordion but no ingredient
    list.  Its body then starts with Nutrition/Dietary/Allergy information.
    Treating that warning text as ingredients would incorrectly upgrade
    ``may contain`` to ``contains``.
    """
    value = clean(value)
    markers = ("Nutrition information", "Dietary information", "Allergy Information")
    if any(value.lower().startswith(marker.lower()) for marker in markers):
        return ""
    positions = [value.lower().find(marker.lower()) for marker in markers]
    positions = [position for position in positions if position > 0]
    return value[:min(positions)].strip() if positions else value


def heading_body(tree, title):
    # Prefer the inner product-information heading. The accordion's outer h2
    # can have the entire panel as its sibling, which would mix ingredients,
    # nutrition and warnings and incorrectly turn warnings into ingredients.
    for tag in ("h3", "h4", "h2"):
        for heading in tree.xpath("//" + tag):
            if clean(heading.text_content()).lower() == title.lower():
                sibling = heading.getnext()
                return sibling if sibling is not None else heading.getparent()
    return None


def matching_allergens(text):
    text = text.lower()
    found = set()
    for allergen, aliases in ALLERGEN_ALIASES.items():
        if any(re.search(r"\b(?:" + alias + r")\b", text, re.I) for alias in aliases):
            found.add(allergen)
    return found


def parse_page(content, expected_name=""):
    tree = html.fromstring(content)
    names = tree.xpath("//h1")
    observed_name = clean(names[0].text_content()) if names else ""
    ingredient_body = heading_body(tree, "Ingredients")
    allergy_body = heading_body(tree, "Allergy Information")
    dietary_body = heading_body(tree, "Dietary information")
    description_body = heading_body(tree, "Description")
    highlights_body = heading_body(tree, "Highlights")
    ingredient_text = clean_ingredient_section(ingredient_body.text_content()) if ingredient_body is not None else ""
    allergy_text = clean(allergy_body.text_content()) if allergy_body is not None else ""
    dietary_text = clean(dietary_body.text_content()) if dietary_body is not None else ""
    product_claims = clean(" ".join(
        body.text_content() for body in (description_body, highlights_body) if body is not None
    ))
    bold_terms = []
    if ingredient_body is not None:
        bold_terms = [clean(node.text_content()) for node in ingredient_body.xpath(".//strong|.//b")]
        bold_terms = [term for term in bold_terms if term and term.lower() not in {"ingredients", "ingredients:"}]

    emphasised_allergens = matching_allergens(" | ".join(bold_terms))
    contained = matching_allergens(ingredient_text)
    # Plant-milk phrases do not declare the regulated milk allergen. Other
    # allergens in the phrase (for example soya, almond or oat) still apply.
    milk_check = re.sub(r"\b(?:coconut|almond|oat|rice|soya|soy|pea)\s+milk\b", "", ingredient_text, flags=re.I)
    if not re.search(r"\b(?:milk|lactose|whey|casein)\b", milk_check, re.I):
        contained.discard("milk")
    warning_text = allergy_text
    precaution_text = re.sub(
        r"for allergens.*?(?:bold|highlighted ingredients)\.?", "", allergy_text, flags=re.I
    )
    warning_marker = re.search(
        r"may\s+(?:also\s+)?contain|produced\s+in\s+.*?uses|packed\s+in\s+.*?handles|factory\s+.*?handles",
        precaution_text,
        re.I,
    )
    may_contain = matching_allergens(precaution_text) if warning_marker else set()
    explicit_free = set()
    claim_text = f"{observed_name} {dietary_text} {product_claims}"
    if re.search(r"\bgluten[ -]?free\b", claim_text, re.I):
        explicit_free.add("cereals_containing_gluten")
    claim_patterns = {
        "celery": r"\bcelery[ -]?free\b",
        "crustaceans": r"\bcrustacean[ -]?free\b",
        "eggs": r"\begg[ -]?free\b",
        "fish": r"\bfish[ -]?free\b",
        "lupin": r"\blupin[ -]?free\b",
        "milk": r"\b(?:milk|dairy)[ -]?free\b",
        "molluscs": r"\bmollusc[ -]?free\b",
        "mustard": r"\bmustard[ -]?free\b",
        "peanuts": r"\bpeanut[ -]?free\b",
        "sesame": r"\bsesame[ -]?free\b",
        "soya": r"\bsoy(?:a)?[ -]?free\b",
        "sulphur_dioxide_sulphites": r"\bsulphite[ -]?free\b",
        "tree_nuts": r"\bnut[ -]?free\b",
    }
    explicit_free.update(a for a, pattern in claim_patterns.items() if re.search(pattern, claim_text, re.I))
    for claim in re.findall(r"free\s+from\s+([^.;]+)", claim_text, re.I):
        explicit_free.update(matching_allergens(claim))
    for claim in re.findall(r"free\s+from\s*:\s*([^.;]+)", allergy_text, re.I):
        explicit_free.update(matching_allergens(claim))
    complete = bool(ingredient_text and allergy_text)
    evidence_status = "label_complete" if complete else (
        "ingredients_only" if ingredient_text else "no_ingredients"
    )
    results = {}
    for allergen in ALLERGEN_ALIASES:
        if allergen in contained:
            basis = "emphasised_ingredient" if allergen in emphasised_allergens else "ingredient_list"
            results[allergen] = ("contains", basis)
        elif allergen in may_contain:
            results[allergen] = ("may_contain", "precautionary_allergen_warning")
        elif allergen in explicit_free:
            results[allergen] = ("free", "explicit_free_from_claim")
        elif complete:
            results[allergen] = ("free", "complete_online_label_no_declaration")
        else:
            results[allergen] = ("unknown", "insufficient_online_label")
    return {
        "observed_name": observed_name,
        "expected_name": expected_name,
        "ingredients_text": ingredient_text,
        "allergen_statement": warning_text,
        "dietary_information": dietary_text,
        "product_claims": product_claims,
        "emphasised_terms": " | ".join(bold_terms),
        "evidence_status": evidence_status,
        "results": results,
    }


def fetch(product, retries=3):
    url = product["source_url"]
    if not hasattr(THREAD_LOCAL, "session"):
        THREAD_LOCAL.session = requests.Session()
        THREAD_LOCAL.session.headers.update({"User-Agent": "GroceryOptimiserDataAudit/1.0"})
    last_error = ""
    for attempt in range(retries):
        try:
            response = THREAD_LOCAL.session.get(url, timeout=30)
            response.raise_for_status()
            content = response.content
            parsed = parse_page(content, product["product_name"])
            parsed["source_content_sha256"] = hashlib.sha256(content).hexdigest()
            parsed["fetch_error"] = ""
            return parsed
        except (OSError, requests.RequestException, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(1 + attempt)
    return {
        "observed_name": "", "expected_name": product["product_name"], "ingredients_text": "",
        "allergen_statement": "", "dietary_information": "", "product_claims": "", "emphasised_terms": "",
        "evidence_status": "fetch_failed", "source_content_sha256": "", "fetch_error": last_error,
        "results": {a: ("unknown", "fetch_failed") for a in ALLERGEN_ALIASES},
    }


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(root=ROOT, workers=4, checked_at=None):
    products = read_csv("data/products.csv", root)
    checked_at = checked_at or date.today().isoformat()
    fetched = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, product): product for product in products}
        for number, future in enumerate(as_completed(futures), start=1):
            product = futures[future]
            fetched[product["product_id"]] = future.result()
            if number % 25 == 0 or number == len(products):
                print(f"fetched {number}/{len(products)}", flush=True)

    evidence_rows, allergen_rows = [], []
    for product in products:
        pid = product["product_id"]
        result = fetched[pid]
        evidence_rows.append({
            "product_id": pid,
            "retailer_product_id": product["retailer_product_id"],
            "checked_at": checked_at,
            "source_url": product["source_url"],
            "observed_name": result["observed_name"],
            "ingredients_text": result["ingredients_text"],
            "allergen_statement": result["allergen_statement"],
            "dietary_information": result["dietary_information"],
            "product_claims": result["product_claims"],
            "emphasised_terms": result["emphasised_terms"],
            "evidence_status": result["evidence_status"],
            "source_content_sha256": result["source_content_sha256"],
            "fetch_error": result["fetch_error"],
        })
        for allergen, (status, basis) in result["results"].items():
            allergen_rows.append({
                "product_id": pid,
                "allergen_id": allergen,
                "status": status,
                "evidence_basis": basis,
                "notes": "",
            })
    write_csv(root / "data/product_allergen_evidence.csv", [
        "product_id", "retailer_product_id", "checked_at", "source_url", "observed_name",
        "ingredients_text", "allergen_statement", "dietary_information", "product_claims", "emphasised_terms",
        "evidence_status", "source_content_sha256", "fetch_error"
    ], evidence_rows)
    write_csv(root / "data/product_allergens.csv", [
        "product_id", "allergen_id", "status", "evidence_basis", "notes"
    ], allergen_rows)
    return evidence_rows, allergen_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--checked-at")
    args = parser.parse_args()
    evidence, allergens = build(workers=max(1, min(args.workers, 16)), checked_at=args.checked_at)
    counts = {}
    for row in allergens:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(f"products assessed: {len(evidence)}")
    print("evidence status:", {s: sum(r['evidence_status'] == s for r in evidence) for s in sorted({r['evidence_status'] for r in evidence})})
    print("allergen statuses:", dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
