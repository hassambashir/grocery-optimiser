"""Regression tests for regulated-allergen evidence and classifications."""
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from catalogue import UK_ALLERGENS, read_csv
from fetch_tesco_allergens import clean_ingredient_section, parse_page
from validate_seed_data import validate


class AllergenParserTests(unittest.TestCase):
    def test_contains_warning_and_absent_allergen(self):
        page = b"""
          <h1>Example noodles</h1>
          <h3>Ingredients</h3><div>Rice, <strong>Wheat</strong>, <strong>Egg</strong></div>
          <h3>Allergy Information</h3><div>May also contain peanuts.</div>
        """
        result = parse_page(page)
        self.assertEqual(result["results"]["cereals_containing_gluten"][0], "contains")
        self.assertEqual(result["results"]["eggs"][0], "contains")
        self.assertEqual(result["results"]["peanuts"][0], "may_contain")
        self.assertEqual(result["results"]["fish"][0], "free")

    def test_explicit_gluten_free_claim_without_complete_label(self):
        page = b"<h1>Example Gluten Free Roll</h1><h3>Description</h3><div>Gluten-free roll.</div>"
        result = parse_page(page)
        self.assertEqual(result["results"]["cereals_containing_gluten"],
                         ("free", "explicit_free_from_claim"))
        self.assertEqual(result["results"]["eggs"][0], "unknown")

    def test_plant_milk_is_not_regulated_milk(self):
        page = b"""
          <h1>Coconut sauce</h1>
          <h3>Ingredients</h3><div>Coconut milk, water</div>
          <h3>Allergy Information</h3><div>For allergens see ingredients in bold.</div>
        """
        self.assertEqual(parse_page(page)["results"]["milk"][0], "free")

    def test_neighbouring_warning_is_not_an_ingredient(self):
        captured = "Dietary information Suitable for Vegans Allergy Information May contain gluten."
        self.assertEqual(clean_ingredient_section(captured), "")


class AllergenCatalogueTests(unittest.TestCase):
    def test_every_product_has_all_fourteen_classifications(self):
        products = read_csv("data/products.csv")
        rows = read_csv("data/product_allergens.csv")
        by_product = {}
        for row in rows:
            by_product.setdefault(row["product_id"], set()).add(row["allergen_id"])
        self.assertEqual(set(by_product), {p["product_id"] for p in products})
        self.assertTrue(all(value == UK_ALLERGENS for value in by_product.values()))
        self.assertEqual(len(rows), len(products) * 14)

    def test_verified_gluten_free_products_are_free_and_mapped(self):
        products = {r["product_id"]: r for r in read_csv("data/products.csv")}
        statuses = {(r["product_id"], r["allergen_id"]): r["status"]
                    for r in read_csv("data/product_allergens.csv")}
        alternatives = read_csv("data/gluten_free_alternatives.csv")
        self.assertGreaterEqual(len(alternatives), 16)
        for alternative in alternatives:
            product = products[alternative["product_id"]]
            self.assertEqual(alternative["ingredient_id"], product["ingredient_id"])
            self.assertEqual(statuses[(product["product_id"], "cereals_containing_gluten")], "free")

    def test_invalid_allergen_status_fails_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "data", root / "data")
            shutil.copytree(ROOT / "config", root / "config")
            path = root / "data/product_allergens.csv"
            rows = read_csv(path, root)
            rows[0]["status"] = "probably_free"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            errors, _ = validate(root)
            self.assertTrue(any("invalid allergen status" in error for error in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
