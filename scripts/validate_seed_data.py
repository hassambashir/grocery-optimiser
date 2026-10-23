"""Validate catalogue integrity and actual optimiser eligibility (offline snapshot)."""
import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from catalogue import (ROOT, read_csv, positive, effective_pack, exclusion_reason,
                       consumption_step, AVAILABILITY, UNITS,
                       MAIN_PROTEINS, PRIMARY_SIDES,
                       INTENTIONAL_RETAIL_COMPOSITES,
                       looks_like_composite_ingredient)


def validate(root=ROOT, allow_documented_exceptions=False):
    errors=[]
    def require(ok,message):
        if not ok:errors.append(message)
    def unique(rows,key,label):
        values=[r.get(key,'') for r in rows]
        require(all(values),f'{label}: blank {key}')
        for v,n in Counter(values).items():require(n==1,f'{label}: duplicate {key} {v}')
    paths=['data/recipes.csv','data/recipe_ingredients.csv','data/ingredients.csv',
           'data/products.csv','data/unit_conversions.csv','config/flexibility_classes.csv',
           'config/initial_inventory.csv','data/product_evidence.csv']
    tables={}
    for path in paths:
        try:tables[path]=read_csv(path,root)
        except (ValueError,OSError,csv.Error) as e:errors.append(str(e))
    if errors:return errors,{}
    recipes,lines,ingredients,products,conversions,flex,inventory,evidence=[tables[p] for p in paths]
    required={
      paths[0]:{'recipe_id','recipe_name','servings','cooking_instructions','main_protein','cooking_method','rating'},
      paths[1]:{'recipe_id','ingredient_id','preferred_quantity','unit'},
      paths[2]:{'ingredient_id','preferred_model_unit','default_flexibility_class','shelf_life_class'},
      paths[3]:{'product_id','retailer_product_id','ingredient_id','retailer','product_name','pack_quantity','pack_unit','usable_quantity','usable_unit','regular_price_gbp','clubcard_price_gbp','availability_status','product_resolution_status','source_url','source_checked_at','notes'},
      paths[4]:{'conversion_id','ingredient_id','source_unit','model_unit','multiplier'},
      paths[5]:{'flexibility_class','min_factor','preferred_factor','max_factor'},
      paths[6]:{'ingredient_id','quantity','unit'},
      paths[7]:{'product_id','retailer_product_id','checked_at','source_url','observed_name','regular_price_gbp','availability_status'}}
    for path,fields in required.items():
        if tables[path]: require(fields<=set(tables[path][0]),f'{path}: missing required columns {fields-set(tables[path][0])}')
        elif path!='config/initial_inventory.csv':errors.append(f'{path}: empty table')
    if errors:return errors,{}
    for rows,key,label in [(recipes,'recipe_id','recipes'),(ingredients,'ingredient_id','ingredients'),(products,'product_id','products'),(products,'retailer_product_id','products'),(conversions,'conversion_id','conversions'),(flex,'flexibility_class','flexibility'),(inventory,'ingredient_id','inventory'),(evidence,'product_id','evidence')]:unique(rows,key,label)
    im={r['ingredient_id']:r for r in ingredients};rm={r['recipe_id']:r for r in recipes};fm={r['flexibility_class']:r for r in flex};em={r['product_id']:r for r in evidence}
    candidate_path=root/'staging/product_candidates.csv'
    if candidate_path.exists():
        candidates=read_csv(candidate_path,root)
        unique(candidates,'product_id','product candidates')
        active_ids={p['product_id'] for p in products}
        for candidate in candidates:
            require(candidate['product_id'] not in active_ids,
                    f"{candidate['product_id']}: candidate product is also active")
    for pair,n in Counter((r['recipe_id'],r['ingredient_id']) for r in lines).items():require(n==1,f'duplicate recipe ingredient {pair}')
    for r in recipes:
        require(r['servings']=='2',f"{r['recipe_id']}: expected two servings")
        for k in ['recipe_name','cooking_instructions','main_protein','cooking_method']:require(bool(r[k].strip()),f"{r['recipe_id']}: blank {k}")
        require(r['main_protein'] in MAIN_PROTEINS,f"{r['recipe_id']}: non-standard main protein {r['main_protein']}")
        require(r['primary_side'] in PRIMARY_SIDES,f"{r['recipe_id']}: non-standard primary side {r['primary_side']}")
        require(any(l['recipe_id']==r['recipe_id'] for l in lines),f"{r['recipe_id']}: no ingredients")
        rating=r.get('rating','').strip()
        if rating:
            try:require(0<=float(rating)<=5,f"{r['recipe_id']}: rating must be from 0 to 5")
            except ValueError:require(False,f"{r['recipe_id']}: rating must be blank or numeric")
    for r in flex:
        keys=['min_factor','preferred_factor','max_factor']
        good=all(positive(r[k]) for k in keys);require(good,f"Invalid flexibility values: {r['flexibility_class']}")
        if good:require(float(r['min_factor'])<=float(r['preferred_factor'])==1<=float(r['max_factor']),f"Invalid flexibility bounds: {r['flexibility_class']}")
    for r in ingredients:
        iid=r['ingredient_id']
        require(r['preferred_model_unit'] in UNITS,f'{iid}: invalid model unit')
        require(r['default_flexibility_class'] in fm,f'{iid}: unknown flexibility class')
        require(r['shelf_life_class'] in {'short','medium','long','unknown'},f'{iid}: invalid shelf life')
        require(not looks_like_composite_ingredient(r) or iid in INTENTIONAL_RETAIL_COMPOSITES,
                f'{iid}: unapproved composite canonical ingredient')
    for r in lines:
        iid=r['ingredient_id'];label=f"{r['recipe_id']}/{iid}"
        require(r['recipe_id'] in rm,f'{label}: unknown recipe');require(iid in im,f'{label}: unknown ingredient')
        require(positive(r['preferred_quantity']),f'{label}: invalid preferred quantity')
        if iid in im:
            require(r['unit']==im[iid]['preferred_model_unit'],f'{label}: recipe/model unit mismatch')
            step=consumption_step(iid,r['unit'])
            if step and positive(r['preferred_quantity']):require(abs(float(r['preferred_quantity'])/step-round(float(r['preferred_quantity'])/step))<1e-8,f'{label}: impractical fractional count')
    # Regression check for the removed coriander-and-mint synthetic ingredient.
    require('fresh_herb_mix_coriander_mint' not in im,
            'fresh_herb_mix_coriander_mint: removed composite ingredient has returned')
    if 'R010' in rm:
        r10={r['ingredient_id'] for r in lines if r['recipe_id']=='R010'}
        require({'fresh_coriander','fresh_mint'}<=r10,
                'R010: coriander and mint must be separate recipe ingredients')
    eligible=defaultdict(list);excluded={}
    for p in products:
        pid=p['product_id'];iid=p['ingredient_id']
        require(iid in im,f'{pid}: unknown ingredient');require(p['retailer']=='Tesco',f'{pid}: retailer must be Tesco')
        require(bool(re.fullmatch(r'\d{9}',p['retailer_product_id'])),f'{pid}: invalid Tesco ID')
        require(p['source_url']=='https://www.tesco.com/shop/en-GB/products/'+p['retailer_product_id'],f'{pid}: URL/ID mismatch')
        require(p['product_resolution_status']=='resolved_exact',f'{pid}: unresolved product')
        require(p['availability_status'] in AVAILABILITY,f'{pid}: unknown availability status')
        require(p['pack_unit'] in UNITS,f'{pid}: invalid pack unit')
        require(positive(p['pack_quantity']),f'{pid}: invalid pack quantity')
        require(positive(p['regular_price_gbp']),f'{pid}: invalid regular price')
        if p['clubcard_price_gbp']:
            require(positive(p['clubcard_price_gbp']),f'{pid}: invalid Clubcard price')
            if positive(p['regular_price_gbp']) and positive(p['clubcard_price_gbp']):require(float(p['clubcard_price_gbp'])<=float(p['regular_price_gbp']),f'{pid}: Clubcard price exceeds regular price')
        require(bool(p['usable_quantity'])==bool(p['usable_unit']),f'{pid}: incomplete usable pair')
        if p['usable_quantity']:
            require(positive(p['usable_quantity']),f'{pid}: invalid usable quantity')
            require(p['usable_unit'] in UNITS,f'{pid}: invalid usable unit')
            if p['pack_unit']==p['usable_unit'] and positive(p['pack_quantity']) and positive(p['usable_quantity']):require(float(p['usable_quantity'])<=float(p['pack_quantity']),f'{pid}: usable quantity exceeds pack')
        try:date.fromisoformat(p['source_checked_at'])
        except ValueError:errors.append(f'{pid}: invalid source date')
        if iid in im:
            require((p['usable_unit'] if p['usable_quantity'] else p['pack_unit'])==im[iid]['preferred_model_unit'],f'{pid}: retail/model unit mismatch')
        if p['pack_unit'] in {'each','cube'} and positive(p['pack_quantity']):require(float(p['pack_quantity']).is_integer(),f'{pid}: fractional retail count')
        reason=exclusion_reason(p,im)
        if reason:excluded[pid]=reason
        else:eligible[iid].append(p)
        e=em.get(pid);require(e is not None,f'{pid}: missing verification evidence')
        if e:
            for pk,ek in [('retailer_product_id','retailer_product_id'),('source_url','source_url'),('product_name','observed_name'),('regular_price_gbp','regular_price_gbp'),('availability_status','availability_status'),('source_checked_at','checked_at')]:require(p[pk]==e[ek],f'{pid}: evidence mismatch {pk}')
            # Tesco sometimes displays drained rather than gross weight as Pack size.
            observed=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(KG|G|ML|L)',e.get('observed_pack',''),re.I)
            if observed:
                q=float(observed[1]);u=observed[2].lower()
                if u in {'kg','l'}:q*=1000;u='g' if u=='kg' else 'ml'
                comparisons=[]
                if p['pack_unit']==u and positive(p['pack_quantity']):comparisons.append(float(p['pack_quantity']))
                if p['usable_unit']==u and positive(p['usable_quantity']):comparisons.append(float(p['usable_quantity']))
                if comparisons:require(any(abs(q-v)<1e-8 for v in comparisons),f'{pid}: quantity contradicts observed pack size')
    require(set(em)=={p['product_id'] for p in products},'Orphan verification evidence')
    for iid in INTENTIONAL_RETAIL_COMPOSITES & set(im):
        require(any(p['ingredient_id']==iid and p['product_resolution_status']=='resolved_exact' for p in products),
                f'{iid}: intentional retail composite lacks a verified Tesco product identity')
    for r in conversions:
        label=r['conversion_id'];require(r['ingredient_id'] in im,f'{label}: unknown conversion ingredient')
        require(positive(r['multiplier']),f'{label}: invalid conversion multiplier')
        require(bool(r['source_unit']) and r['model_unit'] in UNITS,f'{label}: invalid conversion units')
    for key,n in Counter((r['ingredient_id'],r['source_unit'],r['model_unit']) for r in conversions).items():
        require(n==1,f'Duplicate conversion pair: {key}')
    for r in inventory:
        iid=r['ingredient_id'];require(iid in im,f'{iid}: unknown inventory ingredient')
        require(positive(r['quantity'],True),f'{iid}: invalid inventory quantity')
        if iid in im:require(r['unit']==im[iid]['preferred_model_unit'],f'{iid}: inventory/model unit mismatch')
    used={r['ingredient_id'] for r in lines};missing=sorted(used-set(eligible))
    exceptions={}
    ep=root/'data/coverage_exceptions.csv'
    if ep.exists():
        for r in read_csv(ep):
            require(r['ingredient_id'] in used,'Unknown coverage exception ingredient')
            require(bool(r.get('reason')) and bool(r.get('research_urls')), 'Incomplete coverage exception')
            exceptions[r['ingredient_id']]=r
    for iid in missing:
        if not (allow_documented_exceptions and iid in exceptions):errors.append(f'{iid}: NO ELIGIBLE TESCO PRODUCT (inventory is not catalogue coverage)')
    for iid in exceptions:require(iid in missing,f'{iid}: stale coverage exception')
    stats=dict(recipes=len(recipes),used_ingredients=len(used),canonical_ingredients=len(ingredients),recipe_ingredient_rows=len(lines),products=len(products),eligible_products=sum(map(len,eligible.values())),covered_ingredients=len(used&set(eligible)),missing=missing,excluded=excluded,alternatives=sum(max(0,len(eligible[i])-1) for i in used))
    return errors,stats


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-documented-exceptions',action='store_true');args=parser.parse_args()
    errors,stats=validate(allow_documented_exceptions=args.allow_documented_exceptions)
    print('Seed-data validation '+('FAILED' if errors else 'PASSED'))
    for k,v in stats.items():
        if k!='excluded':print(f'{k}: {v}')
    print(f"Excluded product rows: {len(stats.get('excluded',{}))}")
    for e in errors:print('- '+e)
    print('Offline integrity/eligibility check; postcode-specific stock and future prices require checkout verification.')
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
