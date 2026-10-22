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


def run(request):
    errors, _ = validate()
    if errors:
        raise ValueError('; '.join(errors))
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
    # This process handles one solve only; no global patch shared with web requests.
    optimise_week.read_csv = lambda path: tables[path] if path in tables else read_csv(path)
    with contextlib.redirect_stdout(io.StringIO()):
        return optimise_week.solve(days=request['days'], inventory_path='app_inventory',
                                   required_recipes=request['required_recipes'])

if __name__ == '__main__':
    try:
        print(json.dumps(run(json.load(sys.stdin))))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
