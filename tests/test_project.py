"""Regression tests for data failures and decisions, not just solver status."""
import contextlib
import copy
import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from catalogue import read_csv,exclusion_reason,effective_pack
from validate_seed_data import validate
from validate_staging_data import (method_quality_issues, provenance_warnings,
                                   validate as validate_staging)
from optimise_week import solve


def quiet(**kwargs):
    with contextlib.redirect_stdout(io.StringIO()):return solve(**kwargs)


class DataTests(unittest.TestCase):
    def test_real_catalogue_complete(self):
        errors,stats=validate()
        self.assertEqual(errors,[])
        self.assertEqual(stats['recipes'],40)
        self.assertEqual(stats['covered_ingredients'],stats['used_ingredients'])
        self.assertGreater(stats['alternatives'],80)

    def mutate(self,path,fn):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ['data','config']:shutil.copytree(ROOT/name,root/name)
            target=root/path
            rows=read_csv(target)
            fn(rows)
            with target.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            return validate(root)[0]

    def test_invalid_prices_and_quantities_fail(self):
        for key,value in [('regular_price_gbp','0'),('regular_price_gbp','nan'),('usable_quantity','-1'),('pack_quantity','inf')]:
            with self.subTest(key=key,value=value):
                self.assertTrue(self.mutate('data/products.csv',lambda rows:rows[0].update({key:value})))

    def test_ids_references_urls_and_units_fail(self):
        for key,value in [('product_id','P002'),('retailer_product_id','294007923'),('ingredient_id','NONEXISTENT'),('source_url','https://www.tesco.com/shop/en-GB/products/000000000'),('pack_unit','ml'),('availability_status','in_stock_maybe')]:
            with self.subTest(key=key):self.assertTrue(self.mutate('data/products.csv',lambda rows:rows[0].update({key:value})))

    def test_inventory_cannot_hide_missing_purchase_coverage(self):
        errors=self.mutate('data/products.csv',lambda rows:rows.__setitem__(slice(None),[r for r in rows if r['ingredient_id']!='long_grain_rice']))
        self.assertTrue(any('long_grain_rice: NO ELIGIBLE' in e for e in errors))

    def test_drain_and_inventory_corruption_fail(self):
        self.assertTrue(self.mutate('data/products.csv',lambda r:r[0].update(usable_quantity='99999',usable_unit='g')))
        self.assertTrue(self.mutate('config/initial_inventory.csv',lambda r:r[0].update(quantity='-1')))
        self.assertTrue(self.mutate('data/recipe_ingredients.csv',lambda r:r[0].update(preferred_quantity='0.3')))

    def test_malformed_csv_fails(self):
        for content in ['a,b\n1,2,3\n','a,b\n1\n','a,a\n1,2\n','a,b\n"unterminated,2\n']:
            with self.subTest(content=content),tempfile.TemporaryDirectory() as d:
                p=Path(d)/'bad.csv';p.write_text(content)
                with self.assertRaises((ValueError,csv.Error)):read_csv(p)

    def test_unavailable_or_unresolved_products_are_excluded(self):
        im={r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
        p=read_csv('data/products.csv')[0]
        for key,value in [('availability_status','unknown'),('availability_status','out_of_stock'),('product_resolution_status','unresolved')]:
            q=dict(p);q[key]=value;self.assertTrue(exclusion_reason(q,im))

    def test_active_catalogue_has_no_candidate_products(self):
        products=read_csv('data/products.csv')
        self.assertNotIn('mapping_status',products[0])
        self.assertNotIn('package_type',products[0])
        self.assertFalse({'P071','P278'} & {p['product_id'] for p in products})
        candidates=read_csv('staging/product_candidates.csv')
        self.assertEqual({p['product_id'] for p in candidates},{'P071','P278'})

    def test_known_drained_quantities(self):
        p={r['retailer_product_id']:r for r in read_csv('data/products.csv')}
        for rid,usable in [('303887546',102),('303882239',408),('264129006',235),('297021336',235),('314602620',125)]:
            self.assertEqual(effective_pack(p[rid]),(usable,'g'))
        self.assertEqual(effective_pack(p['279695475']),(220,'g'))

    def test_staged_method_quality_and_optional_provenance(self):
        staged=[]
        for path in sorted((ROOT/'staging').glob('recipes_batch_*.csv')):
            staged.extend(read_csv(path))
        failures=[]
        for recipe in staged:
            failures.extend(method_quality_issues(recipe)[0])
        self.assertEqual(failures,[])

        adequate=('Cook the listed ingredients in sequence until tender and fully cooked. '
                  'Reuse the pan where safe, add the finishing ingredients directly to each plate, '
                  'and serve the complete two-person meal while hot with the prepared side.')
        recipe={'recipe_id':'T','cooking_instructions':adequate,'inspiration_url':''}
        self.assertEqual(method_quality_issues(recipe)[0],[])
        self.assertTrue(provenance_warnings(recipe))
        recipe['cooking_instructions']=adequate+' Finish with your garlic mayo sauce.'
        self.assertTrue(any('prepared-component' in x for x in method_quality_issues(recipe)[0]))

    def test_every_staged_ingredient_has_an_eligible_product(self):
        errors,_,stats=validate_staging()
        self.assertEqual(errors,[])
        self.assertEqual(stats['recipes'],160)
        self.assertEqual(stats['missing_product_ingredients'],[])
        self.assertEqual(stats['ingredients_with_eligible_products'],stats['used_ingredients'])

    def test_new_catalogue_units_and_drained_weight(self):
        ingredients={r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
        products={r['retailer_product_id']:r for r in read_csv('data/products.csv')}
        self.assertEqual(ingredients['green_chilli']['preferred_model_unit'],'g')
        self.assertIn('polenta_cornmeal',ingredients)
        self.assertEqual(effective_pack(products['262489095']),(246,'g'))

    def test_direct_toppings_do_not_require_a_sauce_bowl(self):
        recipes={}
        for path in sorted((ROOT/'staging').glob('recipes_batch_*.csv')):
            recipes.update({r['recipe_id']:r for r in read_csv(path)})
        for rid in ['R042','R055','R058','R062']:
            method=recipes[rid]['cooking_instructions'].lower()
            self.assertNotIn('mix chipotle paste with mayonnaise',method)
            self.assertNotIn('mix harissa paste with mayonnaise',method)
            self.assertNotIn('mix sesame seeds into mayonnaise',method)


class OptimiserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=quiet()

    def test_seven_day_real_plan(self):
        p=self.plan
        self.assertEqual(p['status'],'Optimal');self.assertEqual(p['eligible_recipe_count'],40)
        self.assertEqual(len({r['recipe_id'] for r in p['recipes']}),7)
        self.assertGreater(p['spend_gbp'],0)
        self.assertAlmostEqual(p['spend_gbp'],sum(price for _,_,price in p['basket']))
        self.assertTrue(all(isinstance(n,int) and n>0 for _,n,_ in p['basket']))
        im={r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
        for product,_,_ in p['basket']:self.assertFalse(exclusion_reason(product,im))
        self.assertTrue(all(q>=-1e-5 for q in p['ending_inventory'].values()))
        self.assertGreater(len({r['main_protein'] for r in p['recipes']}),2)

    def test_each_of_all_40_recipes_is_feasible(self):
        for r in read_csv('data/recipes.csv'):
            with self.subTest(recipe=r['recipe_id']):
                p=quiet(days=1,required_recipes=[r['recipe_id']])
                self.assertEqual([x['recipe_id'] for x in p['recipes']],[r['recipe_id']])
                expected={x['ingredient_id'] for x in read_csv('data/recipe_ingredients.csv') if x['recipe_id']==r['recipe_id']}
                self.assertEqual({x['ingredient_id'] for x in p['consumption']},expected)

    def test_half_cucumber_half_cube_and_whole_eggs(self):
        p=quiet(days=3,required_recipes=['R017','R015','R018'])
        for i,q in [('cucumber',0.5),('chicken_stock_mix',0.5),('beef_stock_mix',0.5),('egg',1)]:
            self.assertAlmostEqual(sum(r['quantity'] for r in p['consumption'] if r['ingredient_id']==i),q)
        cucumbers=[n for x,n,_ in p['basket'] if x['ingredient_id']=='cucumber']
        self.assertEqual(cucumbers,[1]);self.assertAlmostEqual(p['ending_inventory']['cucumber'],0.5)

    def test_inventory_is_used_and_unrelated_stock_retained(self):
        with tempfile.TemporaryDirectory() as d:
            stock=Path(d)/'stock.csv';stock.write_text('ingredient_id,quantity,unit\nlong_grain_rice,10000,g\nsaffron,2,g\n')
            p=quiet(days=1,required_recipes=['R001'],inventory_path=str(stock))
            self.assertFalse(any(x['ingredient_id']=='long_grain_rice' for x,_,_ in p['basket']))
            self.assertAlmostEqual(p['ending_inventory']['long_grain_rice'],9870)
            self.assertEqual(p['ending_inventory']['saffron'],2)

    def test_alternative_pack_mix_and_leftovers(self):
        # A constructed exact optimum: demand 10, 6-pack GBP4, 4-pack GBP3,
        # 12-pack GBP9. Best is one 6 + one 4; opening 4 changes it to one 6.
        data={
          'data/recipes.csv':[dict(recipe_id='T',recipe_name='test',main_protein='test',cooking_method='test')],
          'data/recipe_ingredients.csv':[dict(recipe_id='T',ingredient_id='egg',preferred_quantity='10',unit='each')],
          'data/ingredients.csv':[dict(ingredient_id='egg',preferred_model_unit='each',default_flexibility_class='fixed',shelf_life_class='long')],
          'config/flexibility_classes.csv':[dict(flexibility_class='fixed',min_factor='1',max_factor='1')],
          'config/initial_inventory.csv':[],
          'data/products.csv':[]}
        for n,price in [(6,4),(4,3),(12,9)]:
            data['data/products.csv'].append(dict(product_id=str(n),ingredient_id='egg',product_name=str(n),retailer='Tesco',regular_price_gbp=str(price),pack_quantity=str(n),pack_unit='each',usable_quantity='',usable_unit='',availability_status='listed_online',product_resolution_status='resolved_exact'))
        with patch('optimise_week.read_csv',side_effect=lambda p:copy.deepcopy(data[p])):
            p=quiet(days=1);self.assertEqual(p['spend_gbp'],7);self.assertEqual({x['product_id']:n for x,n,_ in p['basket']},{'6':1,'4':1})
            data['config/initial_inventory.csv']=[dict(ingredient_id='egg',quantity='4',unit='each')]
            p=quiet(days=1);self.assertEqual(p['spend_gbp'],4)
            data['config/initial_inventory.csv']=[dict(ingredient_id='egg',quantity='9',unit='each')]
            p=quiet(days=1);self.assertEqual(p['spend_gbp'],3);self.assertEqual(p['ending_inventory']['egg'],3)

    def test_no_free_inflation_to_consume_durable_stock(self):
        p=quiet(days=1,required_recipes=['R001'])
        rice=next(x for x in p['consumption'] if x['ingredient_id']=='long_grain_rice')
        self.assertAlmostEqual(rice['quantity'],rice['preferred_quantity'])

    def test_second_week_carry_forward(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'inventory.csv';units={r['ingredient_id']:r['preferred_model_unit'] for r in read_csv('data/ingredients.csv')}
            with path.open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['ingredient_id','quantity','unit'])
                # Durable-only carry-over: no assumption that opened fresh food survives a week.
                im={r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
                for i,q in self.plan['ending_inventory'].items():
                    if q>1e-5 and im[i]['shelf_life_class']=='long':w.writerow([i,q,units[i]])
            p=quiet(inventory_path=str(path));self.assertEqual(len(p['recipes']),7)
            self.assertEqual(p['status'],'Optimal')


if __name__=='__main__':unittest.main(verbosity=2)
