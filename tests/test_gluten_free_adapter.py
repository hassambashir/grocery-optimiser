"""Regression tests for the conservative gluten-free adapter."""
import unittest
from unittest.mock import patch
from app import solver_job
from catalogue import read_csv

class GlutenFreeAdapterTests(unittest.TestCase):
    def request(self, **overrides):
        base = dict(days=1, required_recipes=[], excluded_recipes=[],
                    excluded_ingredients=[], inventory={}, gluten_free=True)
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
            return {'status': 'Optimal'}
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with patch.object(solver_job.optimise_week, 'solve', side_effect=inspect):
                self.assertEqual(solver_job.run(self.request())['status'], 'Optimal')

    def test_default_does_not_filter_products(self):
        def inspect(**kwargs):
            self.assertEqual(len(solver_job.optimise_week.read_csv('data/products.csv')),
                             len(read_csv('data/products.csv')))
            return {'status': 'Optimal'}
        with patch.object(solver_job, 'validate', return_value=([], {})):
            with patch.object(solver_job.optimise_week, 'solve', side_effect=inspect):
                solver_job.run(self.request(gluten_free=False))

if __name__ == '__main__':
    unittest.main()
