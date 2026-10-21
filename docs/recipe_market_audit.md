> Historical audit retained for context. Superseded by [the executed 21 October validation report](validation_report.md) and [complete catalogue coverage](catalogue_coverage.md). Counts and unresolved items below describe an earlier snapshot.

# Recipe-to-market audit — 21 October 2026

Scope: all 40 recipes, 349 ingredient lines, 132 canonical ingredients, and 88 current Tesco product rows. This is a structural audit of the repository catalogue, **not** a live verification of Tesco prices or local availability.

## Corrected in this pass
- Chicken, beef and vegetable stock recipe lines now use practical **half or whole cubes**. Stock cubes are bought in packs of ten; recipe demand and inventory can be fractional. No recipe ingredient requires pre-making liquid stock. Preserve cooking liquid decisions in cooking instructions, not the shopping ingredient.
- Single cream in R013 is **120ml**, not 120g.
- Bay leaves in R014 are **2 each**, not 0.6g.
- Corrected the stock product availability flags to `listed_online`, which restores product eligibility.

## Gaps requiring real Tesco SKU verification
The catalogue does not yet supply the following recipe ingredients with an eligible, priced matching product. No made-up SKU, pack or price should be added.

**Produce:** potatoes, cucumber, tomatoes, broccoli, mushrooms, aubergine, cauliflower, fresh basil, fresh mint, lemongrass.

**Meat, fish and chilled proteins:** chicken mince, beef mince, beef strips, lamb mince, diced lamb, salmon, cod, prawns, tofu, paneer, halloumi, tuna, eggs.

**Grains, bread and pasta:** tortillas, pasta, jasmine rice, basmati rice, spaghetti, egg noodles, rice noodles, orzo, bulgur, flatbreads, pittas, breadcrumbs, plain flour.

**Tins, pulses and sauces:** kidney beans, chickpeas, black beans, chopped tomatoes, passata, tinned lentils, coconut milk, oyster sauce, fish sauce, Thai red curry paste, olives, mustard.

**Dairy:** single cream, butter, cheddar, ricotta, mozzarella, sour cream.

**Oils, spices and pantry:** sumac (listed SKU marked out of stock), ground cumin, vegetable oil, olive oil, Cajun seasoning, vinegar, bay leaves, brown sugar, curry powder, ground cinnamon, dried dill, sugar, red lentils, peas, feta.

## Household quantity / package fit review
- **Stock cubes:** half/whole cubes in recipes, ten-cube boxes in product catalogue. Manufacturer dilution ratio is relevant to flavour, not to grocery quantity conversion.
- **Bay leaves:** count whole leaves; buy one jar or packet.
- **Cream:** recipe in ml; buy a standard carton, with remainder considered for other recipes.
- **Garlic:** recipe quantities in g (3g per clove). Keep gram-based optimiser demand if garlic bulb products have estimated edible gram yield; display equivalent whole cloves in cooking instructions.
- **Cucumbers:** five recipes currently request 300g each as a proxy for one cucumber. Change to whole-item counting when a Tesco cucumber SKU is verified, rather than optimising fictitious 300g cucumber packs.
- **Carrots and regular tomatoes:** retain grams for optimisation and show approximate number of items. Do not force each recipe to use a whole pack.
- **Chopped tomatoes:** 400g in recipes is a sensible standard tin. Keep distinct from fresh tomatoes, cherry tomatoes, passata and purée.
- **Chickpeas / kidney beans / tinned lentils:** recipe quantities must refer to **drained usable weight**, not tin gross weight. Check label before inserting SKU.
- **Pasta, rice, lentils, flour, oils, dried spices:** partial use of ordinary retail packs is normal and not an error; durable inventory should carry forward.
- **Bread, flatbreads, tortillas, pittas, eggs:** recipes can use fewer than the number sold; model purchase pack count separately from recipe demand.
- **Meat/fish:** recipe weights need not equal retail tray weight; offer feasible pack combinations and identify freezer-safe leftovers.
- **Fresh herbs and salad produce:** flag likely waste and prefer sharing across meals when sensible; don't force an ingredient into a recipe just to empty a pack.

## Important remaining validation
1. Verify actual Tesco SKU URLs, current price, pack quantity, stock status and edible/drained yield for each missing ingredient and sensible alternative packs.
2. Audit all ingredient recipe units against SKU units, particularly each-versus-g and ml-versus-g.
3. Audit cooking instructions for obsolete stock-liquid wording. The R001 and R003 cooking text still mentions stock/water as an instruction; decide the liquid from the actual cooking method, not from the purchase model.
4. Run the seed validator and optimiser after filling product gaps. Most later recipes remain ineligible until their ingredients have priced products.
5. Implement human-readable approximate counts for weight-based produce and robust loose-variable-weight purchasing.

**Audit status:** all recipe lines screened; targeted corrections committed; Tesco product mapping and executable validation incomplete.

