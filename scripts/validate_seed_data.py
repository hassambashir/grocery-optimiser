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
                       UK_ALLERGENS, ALLERGEN_STATUSES,
                       ALLERGEN_EVIDENCE_BASES,
                       INTENTIONAL_RETAIL_COMPOSITES,
                       looks_like_composite_ingredient)


def validate(root=ROOT, allow_documented_exceptions=False):
    errors=[]
    def comparable_name(value):
        # Tesco occasionally changes capitalisation or omits a space before
        # the pack size without changing the product identity.
        return re.sub(r'[^a-z0-9]+','',(value or '').lower())
    def require(ok,message):
        if not ok:errors.append(message)
    def unique(rows,key,label):
        values=[r.get(key,'') for r in rows]
        require(all(values),f'{label}: blank {key}')
        for v,n in Counter(values).items():require(n==1,f'{label}: duplicate {key} {v}')
    paths=['data/recipes.csv','data/recipe_ingredients.csv','data/ingredients.csv',
           'data/products.csv','data/unit_conversions.csv','config/flexibility_classes.csv',
           'config/initial_inventory.csv','data/product_evidence.csv',
           'data/allergens.csv','data/product_allergens.csv',
           'data/product_allergen_evidence.csv','data/gluten_free_alternatives.csv']
    tables={}
    for path in paths:
        try:tables[path]=read_csv(path,root)
        except (ValueError,OSError,csv.Error) as e:errors.append(str(e))
    if errors:return errors,{}
    (recipes,lines,ingredients,products,conversions,flex,inventory,evidence,
     allergens,product_allergens,allergen_evidence,gf_alternatives)=[tables[p] for p in paths]
    required={
      paths[0]:{'recipe_id','recipe_name','servings','cooking_instructions','main_protein','cooking_method','rating'},
      paths[1]:{'recipe_id','ingredient_id','preferred_quantity','unit'},
      paths[2]:{'ingredient_id','preferred_model_unit','default_flexibility_class','shelf_life_class'},
      paths[3]:{'product_id','retailer_product_id','ingredient_id','retailer','product_name','pack_quantity','pack_unit','usable_quantity','usable_unit','regular_price_gbp','clubcard_price_gbp','availability_status','product_resolution_status','source_url','source_checked_at','notes'},
      paths[4]:{'conversion_id','ingredient_id','source_unit','model_unit','multiplier'},
      paths[5]:{'flexibility_class','min_factor','preferred_factor','max_factor'},
      paths[6]:{'ingredient_id','quantity','unit'},
      paths[7]:{'product_id','retailer_product_id','checked_at','source_url','observed_name','regular_price_gbp','availability_status'},
      paths[8]:{'allergen_id','regulated_name','notes'},
      paths[9]:{'product_id','allergen_id','status','evidence_basis','notes'},
      paths[10]:{'product_id','retailer_product_id','checked_at','source_url','observed_name','ingredients_text','allergen_statement','dietary_information','product_claims','emphasised_terms','evidence_status','source_content_sha256','fetch_error'},
      paths[11]:{'product_id','ingredient_id','compatibility','quantity_adjustment_required','instruction_adjustment_required','guidance','verified_at'}}
    for path,fields in required.items():
        if tables[path]: require(fields<=set(tables[path][0]),f'{path}: missing required columns {fields-set(tables[path][0])}')
        elif path!='config/initial_inventory.csv':errors.append(f'{path}: empty table')
    if errors:return errors,{}
    for rows,key,label in [(recipes,'recipe_id','recipes'),(ingredients,'ingredient_id','ingredients'),(products,'product_id','products'),(products,'retailer_product_id','products'),(conversions,'conversion_id','conversions'),(flex,'flexibility_class','flexibility'),(inventory,'ingredient_id','inventory'),(evidence,'product_id','evidence'),(allergens,'allergen_id','allergens'),(allergen_evidence,'product_id','allergen evidence'),(gf_alternatives,'product_id','gluten-free alternatives')]:unique(rows,key,label)
    im={r['ingredient_id']:r for r in ingredients};rm={r['recipe_id']:r for r in recipes};fm={r['flexibility_class']:r for r in flex};em={r['product_id']:r for r in evidence}
    pm={r['product_id']:r for r in products};aem={r['product_id']:r for r in allergen_evidence}
    require({r['allergen_id'] for r in allergens}==UK_ALLERGENS,
            'data/allergens.csv must contain exactly the 14 UK regulated allergen groups')
    allergen_pairs=Counter((r['product_id'],r['allergen_id']) for r in product_allergens)
    require(all(n==1 for n in allergen_pairs.values()),'Duplicate product/allergen classification')
    require(set(allergen_pairs)=={(p['product_id'],a) for p in products for a in UK_ALLERGENS},
            'Every product must have exactly one classification for every UK allergen')
    for r in product_allergens:
        label=f"{r['product_id']}/{r['allergen_id']}"
        require(r['product_id'] in pm,f'{label}: unknown product')
        require(r['allergen_id'] in UK_ALLERGENS,f'{label}: unknown allergen')
        require(r['status'] in ALLERGEN_STATUSES,f'{label}: invalid allergen status')
        require(r['evidence_basis'] in ALLERGEN_EVIDENCE_BASES,f'{label}: invalid evidence basis')
        expected={
            'contains':{'emphasised_ingredient','ingredient_list'},
            'may_contain':{'precautionary_allergen_warning'},
            'free':{'explicit_free_from_claim','complete_online_label_no_declaration'},
            'unknown':{'insufficient_online_label','fetch_failed'},
        }
        if r['status'] in expected:require(r['evidence_basis'] in expected[r['status']],f'{label}: status/evidence mismatch')
    require(set(aem)==set(pm),'Allergen evidence must cover every product exactly once')
    for pid,e in aem.items():
        require(pid in pm,f'{pid}: orphan allergen evidence')
        if pid not in pm:
            continue
        p=pm[pid]
        require(e['retailer_product_id']==p['retailer_product_id'],f'{pid}: allergen evidence Tesco ID mismatch')
        require(e['source_url']==p['source_url'],f'{pid}: allergen evidence URL mismatch')
        try:date.fromisoformat(e['checked_at'])
        except ValueError:errors.append(f'{pid}: invalid allergen evidence date')
        require(e['evidence_status'] in {'label_complete','ingredients_only','no_ingredients','fetch_failed'},f'{pid}: invalid allergen evidence status')
        if e['evidence_status']=='fetch_failed':
            require(bool(e['fetch_error']),f'{pid}: failed allergen fetch lacks an error')
            require(all(r['status']=='unknown' for r in product_allergens if r['product_id']==pid),f'{pid}: failed fetch must remain unknown')
        else:
            require(comparable_name(e['observed_name'])==comparable_name(p['product_name']),
                    f'{pid}: allergen evidence product-name mismatch')
            require(bool(re.fullmatch(r'[0-9a-f]{64}',e['source_content_sha256'])),f'{pid}: invalid allergen evidence content hash')
    pa={(r['product_id'],r['allergen_id']):r for r in product_allergens}
    for r in gf_alternatives:
        pid=r['product_id'];label=f'{pid}: gluten-free alternative'
        require(pid in pm,f'{label} has unknown product')
        if pid in pm:
            require(r['ingredient_id']==pm[pid]['ingredient_id'],f'{label} ingredient mapping mismatch')
            require(not exclusion_reason(pm[pid],im),f'{label} is not eligible for purchasing')
        require(r['compatibility']=='direct',f'{label} must be a direct compatible product')
        require(r['quantity_adjustment_required'] in {'yes','no'},f'{label} invalid quantity-adjustment flag')
        require(r['instruction_adjustment_required'] in {'yes','no'},f'{label} invalid instruction-adjustment flag')
        require(bool(r['guidance']),f'{label} missing guidance')
        try:date.fromisoformat(r['verified_at'])
        except ValueError:errors.append(f'{label} invalid verification date')
        require(pa.get((pid,'cereals_containing_gluten'),{}).get('status')=='free',f'{label} lacks verified gluten-free status')
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
    products_with_unknown={r['product_id'] for r in product_allergens if r['status']=='unknown'}
    stats=dict(recipes=len(recipes),used_ingredients=len(used),canonical_ingredients=len(ingredients),recipe_ingredient_rows=len(lines),products=len(products),eligible_products=sum(map(len,eligible.values())),covered_ingredients=len(used&set(eligible)),missing=missing,excluded=excluded,alternatives=sum(max(0,len(eligible[i])-1) for i in used),allergen_assessed_products=len(aem),allergen_classifications=len(product_allergens),fully_classified_products=len(products)-len(products_with_unknown),products_with_unknown_allergens=len(products_with_unknown),allergen_fetch_failures=sum(e['evidence_status']=='fetch_failed' for e in allergen_evidence),gluten_free_alternatives=len(gf_alternatives),gluten_free_ingredient_mappings=len({r['ingredient_id'] for r in gf_alternatives}))
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
