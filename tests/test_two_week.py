"""Locked historical simulation and a fresh second-week solve."""
import hashlib
import json
import re
import unittest
from collections import defaultdict
from test_project import ROOT, quiet, read_csv, effective_pack, exclusion_reason


def nonzero(values):
    return {i:q for i,q in values.items() if q>1e-6}


class TwoWeekTests(unittest.TestCase):
    def test_locked_snapshots_and_report(self):
        manifest=json.loads((ROOT/'runs/manifest.json').read_text())
        for path,digest in manifest['sha256'].items():
            # Historical run artifacts are immutable. Input-data digests remain
            # provenance for the execution commit, but the live catalogue is
            # expected to evolve and must not invalidate an old simulation.
            if path.startswith('runs/'):
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        first=json.loads((ROOT/'runs/week_01/plan.json').read_text())
        report=(ROOT/'docs/validation_report.md').read_text()
        recorded={i:float(q) for i,q in re.findall(r'^  (\w+): ([\d.]+) \w+$',report.split('Ending inventory (nonzero):')[1],re.M)}
        self.assertEqual(nonzero(first['ending_inventory']),recorded)
        self.assertEqual(len(recorded),24)
        self.assertEqual(recorded['long_grain_rice'],10000)
        self.assertAlmostEqual(first['spend_gbp'],39.88)
        consumption={(x['recipe_id'],x['ingredient_id']):(x['preferred_quantity'],x['quantity'],x['unit']) for x in first['consumption']}
        self.assertEqual(consumption,{(rid,i):(float(pref),float(q),u) for rid,i,pref,q,u in re.findall(r'^  (R\d+) (\w+): ([\d.]+) -> ([\d.]+) (\w+)$',report,re.M)})
        for product,n,cost in first['basket']:
            self.assertIn(f"{n} x {product['product_name']} |",report)
            self.assertAlmostEqual(cost,n*float(product['regular_price_gbp']))
        self.assertEqual((ROOT/'runs/week_01/ending_inventory.csv').read_bytes(),(ROOT/'runs/week_02/opening_inventory.csv').read_bytes())

    def assert_balances(self,p,require_current_catalogue=False):
        ingredients={r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
        products={r['product_id']:r for r in read_csv('data/products.csv')}
        balance=defaultdict(float,p['opening_inventory'])
        self.assertEqual(p['status'],'Optimal')
        self.assertEqual(len({r['recipe_id'] for r in p['recipes']}),7)
        for product,n,cost in p['basket']:
            self.assertIn(product['product_id'],products)
            if require_current_catalogue:
                self.assertEqual(product,products[product['product_id']])
                self.assertFalse(exclusion_reason(product,ingredients))
            else:
                self.assertEqual(product['retailer'],'Tesco')
                self.assertEqual(product['product_resolution_status'],'resolved_exact')
                self.assertEqual(product['availability_status'],'listed_online')
                self.assertGreater(float(product['regular_price_gbp']),0)
            self.assertIsInstance(n,int);self.assertGreater(n,0)
            self.assertAlmostEqual(cost,n*float(product['regular_price_gbp']))
            balance[product['ingredient_id']]+=n*effective_pack(product)[0]
        for row in p['consumption']:balance[row['ingredient_id']]-=row['quantity']
        for i in set(balance)|set(p['ending_inventory']):
            self.assertGreaterEqual(balance[i],-1e-5)
            self.assertAlmostEqual(balance[i],p['ending_inventory'].get(i,0),places=4)

    def test_complete_two_week_workflow(self):
        first=json.loads((ROOT/'runs/week_01/plan.json').read_text())
        saved=json.loads((ROOT/'runs/week_02/plan.json').read_text())
        current=quiet(inventory_path=str(ROOT/'runs/week_01/ending_inventory.csv'))
        for p in [first,saved]:self.assert_balances(p)
        self.assert_balances(current,require_current_catalogue=True)
        for p in [saved,current]:
            self.assertEqual(nonzero(p['opening_inventory']),nonzero(first['ending_inventory']))
            self.assertAlmostEqual(p['objective'],saved['objective'],places=5)
            self.assertFalse(any(x['ingredient_id']=='cucumber' for x,_,_ in p['basket']))
            self.assertEqual(p['ending_inventory']['long_grain_rice'],10000)
        for week,p in [('week_01',first),('week_02',saved)]:
            exported={r['ingredient_id']:float(r['quantity']) for r in read_csv(ROOT/f'runs/{week}/ending_inventory.csv')}
            self.assertEqual(exported,nonzero(p['ending_inventory']))
