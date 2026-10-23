"""Shared strict CSV reading and purchasing eligibility for validation and solving."""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED_MAPPINGS = {'direct', 'direct_variable_weight', 'effective_usable_quantity',
                     'estimated_usable_weight'}
MAPPINGS = APPROVED_MAPPINGS | {'compatible_candidate', 'substitution_candidate'}
AVAILABILITY = {'listed_online', 'out_of_stock', 'unknown'}
UNITS = {'g', 'ml', 'each', 'cube', 'clove'}
MAIN_PROTEINS = {
    'chicken', 'turkey', 'pork', 'beef', 'lamb', 'fish', 'shrimp',
    'tofu', 'cheese', 'legumes', 'vegetable'
}
PRIMARY_SIDES = {
    'rice', 'potato', 'sweet_potato', 'pasta', 'noodles', 'tortilla',
    'bread', 'couscous', 'bulgur', 'legumes', 'vegetables', 'salad',
    'pastry', 'polenta'
}


def read_csv(path, root=ROOT):
    path = Path(path)
    with (root / path).open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle, strict=True)
        fields = reader.fieldnames
        if not fields or len(fields) != len(set(fields)) or any(not f for f in fields):
            raise ValueError(f'{path}: missing or duplicate column headers')
        result = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'{path}:{reader.line_num}: incorrect column count')
            result.append(row)
        return result


def positive(value, allow_zero=False):
    try:
        n = float(value)
        return math.isfinite(n) and (n >= 0 if allow_zero else n > 0)
    except (TypeError, ValueError):
        return False


def effective_pack(product):
    if product.get('usable_quantity'):
        return float(product['usable_quantity']), product['usable_unit']
    return float(product['pack_quantity']), product['pack_unit']


def exclusion_reason(product, ingredients):
    iid = product.get('ingredient_id')
    if iid not in ingredients:
        return 'unknown ingredient'
    if product.get('retailer') != 'Tesco':
        return 'not Tesco'
    if product.get('product_resolution_status') != 'resolved_exact':
        return 'unresolved product identity'
    if product.get('mapping_status') not in APPROVED_MAPPINGS:
        return 'unapproved substitution or compatibility'
    if product.get('availability_status') != 'listed_online':
        return 'not listed as available in snapshot'
    if not positive(product.get('regular_price_gbp')):
        return 'invalid regular price'
    if not positive(product.get('pack_quantity')):
        return 'invalid pack quantity'
    if bool(product.get('usable_quantity')) != bool(product.get('usable_unit')):
        return 'incomplete usable quantity/unit pair'
    if product.get('usable_quantity') and not positive(product['usable_quantity']):
        return 'invalid usable quantity'
    _, unit = effective_pack(product)
    if unit != ingredients[iid]['preferred_model_unit']:
        return 'model unit mismatch'
    return ''


def consumption_step(ingredient_id, unit):
    # Retail packs always remain integer; kitchen consumption has separate rules.
    if unit == 'cube' or ingredient_id == 'cucumber':
        return 0.5
    return 1.0 if unit == 'each' else None
