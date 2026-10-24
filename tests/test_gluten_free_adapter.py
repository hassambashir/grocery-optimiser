"""Gluten-first allergen policy and solver adapter regression tests."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalogue import read_csv
from app import solver_job
from app.allergen_policy import prepare


class GlutenFreeAdapterTests(unittest.TestCase):
    def request(self, **overrides):
        base = dict(days=1, required_recipes=[], excluded_recipes=[],
                    excluded_ingredients=[], inventory={},
                    allergen_rules={"cereals_containing_gluten": "strict"})
        return {**base, **overrides}

    def test_inventory_without_provenance_fails_closed(self):
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with self.assertRaisesRegex(ValueError, 'product-verified inventory'):
                solver_job.run(self.request(inventory={'rice': 100}))

    def test_only_free_products_reach_solver(self):
        statuses = {r['product_id']: r['status'] for r in read_csv('data/product_allergens.csv')
                    if r['allergen_id'] == 'cereals_containing_gluten'}
        def inspect(**kwargs):
            candidates = solver_job.optimise_week.read_csv('data/products.csv')
            self.assertTrue(candidates)
            self.assertTrue(all(statuses[p['product_id']] == 'free' for p in candidates))
            self.assertTrue(all(v == 0 for v in kwargs['product_penalties'].values()))
            return {'status': 'Optimal'}
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with patch.object(solver_job.optimise_week, 'solve', side_effect=inspect):
                result = solver_job.run(self.request())
        self.assertEqual(result['status'], 'Optimal')
        self.assertIn('unavailable_recipes', result['allergen_coverage'])

    def test_default_does_not_filter_products(self):
        def inspect(**kwargs):
            self.assertEqual(len(solver_job.optimise_week.read_csv('data/products.csv')),
                             len(read_csv('data/products.csv')))
            self.assertTrue(all(v == 0 for v in kwargs['product_penalties'].values()))
            return {'status': 'Optimal'}
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with patch.object(solver_job.optimise_week, 'solve', side_effect=inspect):
                solver_job.run(self.request(allergen_rules={}))

    def test_preference_keeps_products_and_penalises(self):
        def inspect(**kwargs):
            self.assertEqual(len(solver_job.optimise_week.read_csv('data/products.csv')),
                             len(read_csv('data/products.csv')))
            self.assertTrue(any(v > 0 for v in kwargs['product_penalties'].values()))
            return {'status': 'Optimal'}
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with patch.object(solver_job.optimise_week, 'solve', side_effect=inspect):
                solver_job.run(self.request(allergen_rules={'cereals_containing_gluten': 'preference'}))

    def test_missing_ingredient_reports_recipe_unavailable(self):
        products = [{'product_id':'p1','ingredient_id':'rice','regular_price_gbp':'1'}]
        ingredients = {'rice': {'ingredient_id':'rice'}, 'noodles': {'ingredient_id':'noodles'}}
        recipes = [{'recipe_id':'r1'}]
        lines = [{'recipe_id':'r1','ingredient_id':'noodles'}]
        with patch('catalogue.exclusion_reason', return_value=None):
            policy = prepare(products, [], {'cereals_containing_gluten':'strict'},
                             ingredients, recipes, lines)
        self.assertEqual(policy['unavailable_recipes']['r1'], ['noodles'])
        self.assertEqual(policy['products'], [])

    def test_unknown_allowed_only_in_preference(self):
        p = [{'product_id':'p1','ingredient_id':'rice'}]
        with patch('catalogue.exclusion_reason', return_value=None):
            strict = prepare(p, [], {'cereals_containing_gluten':'strict'}, {}, [], [])
            soft = prepare(p, [], {'cereals_containing_gluten':'preference'}, {}, [], [])
        self.assertEqual(strict['products'], [])
        self.assertEqual(soft['product_penalties']['p1'], 2.0)


if __name__ == '__main__':
    unittest.main()
