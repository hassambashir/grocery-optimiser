"""Isolated adapter: preserve the audited CLI solver and its default behaviour."""
import contextlib
import io
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import optimise_week
from catalogue import read_csv
from validate_seed_data import validate
from app.allergen_policy import prepare


def run(request):
    errors, _ = validate()
    if errors:
        raise ValueError('; '.join(errors))
    allergen_rules = request.get('allergen_rules', {})
    if not isinstance(allergen_rules, dict) or any(v not in ('strict', 'preference') for v in allergen_rules.values()):
        raise ValueError('Invalid allergen rules.')
    recipes = read_csv('data/recipes.csv')
    lines = read_csv('data/recipe_ingredients.csv')
    excluded = set(request['excluded_recipes'])
    excluded_ingredients = set(request['excluded_ingredients'])
    excluded.update(r['recipe_id'] for r in lines if r['ingredient_id'] in excluded_ingredients)
    allowed = {r['recipe_id'] for r in recipes} - excluded
    if set(request['required_recipes']) - allowed:
        raise ValueError('A required recipe conflicts with an exclusion.')
    units = {r['ingredient_id']: r['preferred_model_unit'] for r in read_csv('data/ingredients.csv')}
    tables = {
        'data/recipes.csv': [r for r in recipes if r['recipe_id'] in allowed],
        'data/recipe_ingredients.csv': [r for r in lines if r['recipe_id'] in allowed],
        'app_inventory': [dict(ingredient_id=i, quantity=str(q), unit=units[i]) for i,q in request['inventory'].items() if q>0],
    }
    policy = prepare(read_csv('data/products.csv'),
                     read_csv('data/product_allergens.csv'),
                     allergen_rules,
                     {r['ingredient_id']: r for r in read_csv('data/ingredients.csv')},
                     tables['data/recipes.csv'], tables['data/recipe_ingredients.csv'],
                     request['inventory'])
    tables['data/products.csv'] = policy['products']
    # This process handles one solve only; no global patch shared with web requests.
    original_read_csv = optimise_week.read_csv
    try:
        optimise_week.read_csv = lambda path: tables[path] if path in tables else read_csv(path)
        with contextlib.redirect_stdout(io.StringIO()):
            result = optimise_week.solve(days=request['days'], inventory_path='app_inventory',
                                         required_recipes=request['required_recipes'],
                                         product_penalties=policy['product_penalties'])
        result['allergen_coverage'] = {
            'unavailable_recipes': policy['unavailable_recipes'],
            'excluded_product_count': sum(map(len, policy['excluded_products'].values())),
            'eligible_product_count': len(policy['products'])}
        return result
    finally:
        optimise_week.read_csv = original_read_csv

if __name__ == '__main__':
    try:
        print(json.dumps(run(json.load(sys.stdin))))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
