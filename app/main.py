"""Authenticated, single-household API and mobile web interface."""
import json
import os
import secrets
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import date
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select, update
from app.database import connect, households, batches, events, plans, now

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from catalogue import read_csv, effective_pack

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class Login(Input):
    password: str
class Stock(Input):
    request_id: str = Field(min_length=8, max_length=100)
    revision: int = Field(ge=0)
    ingredient_id: str
    action: str = Field(pattern='^(add|set|discard)$')
    quantity: float = Field(ge=0, le=1000000)
    expires_on: date | None = None
    note: str = Field(default='', max_length=500)
class Preferences(Input):
    excluded_ingredients: list[str] = Field(default_factory=list)
    excluded_recipes: list[str] = Field(default_factory=list)
    avoid_previous_plan: bool = False
    allergen_rules: dict[str, str] = Field(default_factory=dict)
class Generate(Input):
    days: int = Field(default=7, ge=1, le=7)
    required_recipes: list[str] = Field(default_factory=list)
class Receipt(Input):
    request_id: str = Field(min_length=8, max_length=100)
    packs: dict[str, int]
class Meals(Input):
    request_id: str = Field(min_length=8, max_length=100)
    cooked: list[str]
    skipped: list[str] = Field(default_factory=list)


def create_app(database_url=None, password=None, session_secret=None, secure_cookie=None):
    password = password or os.environ.get('APP_PASSWORD')
    session_secret = session_secret or os.environ.get('SESSION_SECRET')
    if not password or len(password)<12 or not session_secret or len(session_secret)<32:
        raise RuntimeError('Set APP_PASSWORD (12+ characters) and SESSION_SECRET (32+ characters).')
    url = database_url or os.environ.get('DATABASE_URL','sqlite:///grocery.db')
    engine = connect(url)
    api = FastAPI(title='Grocery Optimiser', docs_url=None, redoc_url=None)
    api.state.engine = engine
    api.add_middleware(SessionMiddleware, secret_key=session_secret, same_site='strict',
        https_only=secure_cookie if secure_cookie is not None else os.environ.get('COOKIE_SECURE','true')=='true', max_age=86400)
    ingredients = {r['ingredient_id']:r for r in read_csv('data/ingredients.csv')}
    recipes = {r['recipe_id']:r for r in read_csv('data/recipes.csv')}
    allergen_status = {(r['product_id'], r['allergen_id']): r['status'] for r in read_csv('data/product_allergens.csv')}
    solve_lock = threading.Lock()
    login_attempts = deque(maxlen=20)
    login_lock = threading.Lock()

    def validate_ids(ids, known):
        if set(ids)-set(known):
            raise HTTPException(422, 'Unknown IDs: '+', '.join(sorted(set(ids)-set(known))))
        if len(ids)!=len(set(ids)):
            raise HTTPException(422, 'Duplicate IDs are not allowed.')

    def home(conn):
        return conn.execute(select(households).where(households.c.id=='home')).mappings().one()

    def lock(conn):
        # Serialises stock mutations across processes in SQLite and PostgreSQL.
        conn.execute(update(households).where(households.c.id=='home').values(revision=households.c.revision+1))

    def stock_rows(conn):
        return [dict(r) for r in conn.execute(select(batches).where(batches.c.household_id=='home',batches.c.quantity>1e-6)).mappings()]

    def verified_stock(conn, rules):
        strict = [a for a, mode in rules.items() if mode == 'strict']
        result = {}
        for r in stock_rows(conn):
            if r['expires_on'] and r['expires_on'] < date.today().isoformat(): continue
            # Legacy purchases and manual entries have no product evidence.
            source = r['source']
            pid = source.rsplit(' product:', 1)[-1] if ' product:' in source else None
            if strict and (not pid or any(allergen_status.get((pid, a), 'unknown') != 'free' for a in strict)):
                continue
            result[r['ingredient_id']] = result.get(r['ingredient_id'], 0) + r['quantity']
        return result

    def available(conn):
        result={}
        for r in stock_rows(conn):
            if r['expires_on'] and r['expires_on']<date.today().isoformat():continue
            result[r['ingredient_id']]=result.get(r['ingredient_id'],0)+r['quantity']
        return result

    def add(conn, i, q, source, expires=None):
        if q>0:
            conn.execute(batches.insert().values(id=str(uuid4()),household_id='home',ingredient_id=i,
                quantity=q,unit=ingredients[i]['preferred_model_unit'],created_at=now(),expires_on=expires,source=source))

    def take(conn,i,q,include_expired=False):
        rows=[r for r in stock_rows(conn) if r['ingredient_id']==i and
              (include_expired or not r['expires_on'] or r['expires_on']>=date.today().isoformat())]
        if sum(r['quantity'] for r in rows)+1e-5<q:
            raise HTTPException(409,f'Not enough usable {i}. Record missing purchases or correct your stock first.')
        for r in sorted(rows,key=lambda r:(r['expires_on'] or '9999-12-31',r['created_at'])):
            used=min(q,r['quantity']);q-=used
            conn.execute(update(batches).where(batches.c.id==r['id']).values(quantity=max(0,r['quantity']-used)))
            if q<1e-6:break

    def repeated(conn,key,payload):
        row=conn.execute(select(events).where(events.c.id==key)).mappings().first()
        if row:
            if row['payload']!=payload:raise HTTPException(409,'Request identifier was already used for a different change.')
            return True
        return False

    def record(conn,key,kind,payload,changes):
        conn.execute(events.insert().values(id=key,household_id='home',created_at=now(),kind=kind,payload=payload,changes=changes))

    def get_plan(conn,pid):
        p=conn.execute(select(plans).where(plans.c.id==pid,plans.c.household_id=='home')).mappings().first()
        if not p:raise HTTPException(404,'Plan not found.')
        return dict(p)

    @api.middleware('http')
    async def protect(request, call_next):
        if request.method in {'POST','PUT','DELETE'} and request.headers.get('x-grocery-request')!='1':
            return JSONResponse({'detail':'Missing request header.'},status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    # Dependency reads signed session after SessionMiddleware has populated it.
    from fastapi import Depends
    def auth(request:Request):
        if not request.session.get('household'):raise HTTPException(401,'Please sign in.')

    @api.post('/api/login')
    def login(body:Login,request:Request):
        with login_lock:
            while login_attempts and time.monotonic()-login_attempts[0]>60:login_attempts.popleft()
            if len(login_attempts)>=20:raise HTTPException(429,'Too many login attempts. Try again in a minute.')
            login_attempts.append(time.monotonic())
        if not secrets.compare_digest(body.password.encode(),password.encode()):raise HTTPException(401,'Incorrect password.')
        request.session.clear();request.session['household']='home'
        return {'ok':True}

    @api.post('/api/logout')
    def logout(request:Request):
        request.session.clear();return {'ok':True}

    @api.get('/health')
    def health():return {'status':'ok'}

    @api.get('/api/state',dependencies=[Depends(auth)])
    def state():
        with engine.connect() as conn:
            h=home(conn)
            return {'revision':h['revision'],'preferences':h['preferences'], 'inventory':available(conn),
                'batches':stock_rows(conn),'plans':[dict(p) for p in conn.execute(select(plans).where(plans.c.household_id=='home').order_by(plans.c.created_at.desc())).mappings()],
                'events':[dict(e) for e in conn.execute(select(events).where(events.c.household_id=='home').order_by(events.c.created_at.desc()).limit(100)).mappings()]}

    @api.get('/api/catalogue',dependencies=[Depends(auth)])
    def catalogue():
        return {'ingredients':list(ingredients.values()),'recipes':list(recipes.values()),'recipe_ingredients':read_csv('data/recipe_ingredients.csv')}

    @api.post('/api/stock',dependencies=[Depends(auth)])
    def stock(body:Stock):
        validate_ids([body.ingredient_id],ingredients)
        payload={'operation':'stock',**body.model_dump(mode='json')}
        with engine.begin() as conn:
            lock(conn)
            if repeated(conn,body.request_id,payload):return {'ok':True,'replayed':True}
            if home(conn)['revision']!=body.revision+1:raise HTTPException(409,'Stock changed. Refresh before editing.')
            i=body.ingredient_id;q=body.quantity
            before=sum(r['quantity'] for r in stock_rows(conn) if r['ingredient_id']==i)
            if body.action=='set':
                take(conn,i,before,True);add(conn,i,q,'manual correction',str(body.expires_on) if body.expires_on else None)
            elif body.action=='add':add(conn,i,q,'manual addition',str(body.expires_on) if body.expires_on else None)
            else:take(conn,i,q,True)
            after=sum(r['quantity'] for r in stock_rows(conn) if r['ingredient_id']==i)
            record(conn,body.request_id,'stock',payload,{i:after-before})
        return {'ok':True}

    @api.put('/api/preferences',dependencies=[Depends(auth)])
    def preferences(body:Preferences):
        validate_ids(body.excluded_ingredients,ingredients);validate_ids(body.excluded_recipes,recipes)
        from catalogue import UK_ALLERGENS
        if set(body.allergen_rules)-UK_ALLERGENS or any(v not in ('strict','preference') for v in body.allergen_rules.values()):
            raise HTTPException(422,'Invalid allergen restriction.')
        with engine.begin() as conn:
            lock(conn);conn.execute(update(households).where(households.c.id=='home').values(preferences=body.model_dump()))
        return {'ok':True}

    @api.post('/api/plans',dependencies=[Depends(auth)])
    def generate(body:Generate):
        validate_ids(body.required_recipes,recipes)
        if len(body.required_recipes)>body.days:raise HTTPException(422,'More required recipes than dinners.')
        with engine.connect() as conn:
            h=home(conn);prefs=h['preferences'];revision=h['revision'];inventory=verified_stock(conn,prefs.get('allergen_rules',{}))
            excluded=set(prefs['excluded_recipes'])
            if prefs['avoid_previous_plan']:
                previous=conn.execute(select(plans).where(plans.c.receipts_confirmed==1).order_by(plans.c.created_at.desc())).mappings().first()
                if previous:excluded.update(r['recipe_id'] for r in previous['result']['recipes'])
        params={**body.model_dump(),'excluded_ingredients':prefs['excluded_ingredients'],'excluded_recipes':sorted(excluded),'inventory':inventory,'allergen_rules':prefs.get('allergen_rules',{})}
        if not solve_lock.acquire(blocking=False):raise HTTPException(409,'Another plan is being calculated. Try again shortly.')
        try:
            process=subprocess.run([sys.executable,'-m','app.solver_job'],input=json.dumps(params),text=True,capture_output=True,cwd=ROOT,timeout=120)
        except subprocess.TimeoutExpired:
            raise HTTPException(422,'No plan completed within two minutes. Try fewer requirements.')
        finally:solve_lock.release()
        if process.returncode:raise HTTPException(422,process.stderr.strip()[-1000:])
        result=json.loads(process.stdout);pid=str(uuid4())
        with engine.begin() as conn:
            lock(conn)
            if home(conn)['revision']!=revision+1:raise HTTPException(409,'Your stock or preferences changed during planning. Generate again.')
            conn.execute(plans.insert().values(id=pid,household_id='home',created_at=now(),opening_revision=revision,
                parameters=params,result=result,receipts_confirmed=0,archived=0,meal_status={}))
        return {'id':pid,'result':result}

    @api.post('/api/plans/{pid}/receipts',dependencies=[Depends(auth)])
    def receipts(pid:str,body:Receipt):
        payload={'operation':'receipts','plan_id':pid,**body.model_dump()}
        with engine.begin() as conn:
            lock(conn)
            if repeated(conn,body.request_id,payload):return {'ok':True,'replayed':True}
            p=get_plan(conn,pid)
            if p['archived']:raise HTTPException(409,'This draft was abandoned. Generate a new plan.')
            if p['receipts_confirmed']:raise HTTPException(409,'Purchases already recorded for this plan.')
            basket={x['product_id']:(x,n) for x,n,_ in p['result']['basket']}
            if set(body.packs)!=set(basket):raise HTTPException(422,'Confirm a quantity for every basket line, including zero for missing items.')
            changes={}
            for product_id,n in body.packs.items():
                if n<0 or n>1000:raise HTTPException(422,'Pack quantities must be whole numbers between 0 and 1000.')
                product,_=basket[product_id];q=effective_pack(product)[0]*n;i=product['ingredient_id']
                add(conn,i,q,'purchase '+pid+' product:'+product_id);changes[i]=changes.get(i,0)+q
            conn.execute(update(plans).where(plans.c.id==pid).values(receipts_confirmed=1))
            record(conn,body.request_id,'purchase',payload,changes)
        return {'ok':True}

    @api.post('/api/plans/{pid}/meals',dependencies=[Depends(auth)])
    def meals(pid:str,body:Meals):
        payload={'operation':'meals','plan_id':pid,**body.model_dump()}
        with engine.begin() as conn:
            lock(conn)
            if repeated(conn,body.request_id,payload):return {'ok':True,'replayed':True}
            p=get_plan(conn,pid)
            if p['archived']:raise HTTPException(409,'This draft was abandoned.')
            ids=[r['recipe_id'] for r in p['result']['recipes']]
            validate_ids(body.cooked+body.skipped,ids)
            if not body.cooked and not body.skipped:raise HTTPException(422,'Choose at least one meal.')
            statuses=dict(p['meal_status'])
            if set(statuses)&set(body.cooked+body.skipped):raise HTTPException(409,'One of these meals has already been recorded.')
            demand={}
            for row in p['result']['consumption']:
                if row['recipe_id'] in body.cooked:
                    i=row['ingredient_id'];demand[i]=demand.get(i,0)+row['quantity']
            for i,q in demand.items():take(conn,i,q)
            statuses.update({r:'cooked' for r in body.cooked});statuses.update({r:'skipped' for r in body.skipped})
            conn.execute(update(plans).where(plans.c.id==pid).values(meal_status=statuses))
            record(conn,body.request_id,'meals',payload,{i:-q for i,q in demand.items()})
        return {'ok':True}

    @api.post('/api/plans/{pid}/abandon',dependencies=[Depends(auth)])
    def abandon(pid:str):
        with engine.begin() as conn:
            lock(conn);p=get_plan(conn,pid)
            if p['receipts_confirmed'] or p['meal_status']:raise HTTPException(409,'An active plan cannot be abandoned. Record any remaining meals as skipped.')
            conn.execute(update(plans).where(plans.c.id==pid).values(archived=1))
        return {'ok':True}

    @api.get('/')
    def index():return FileResponse(ROOT/'app/static/index.html')
    api.mount('/static',StaticFiles(directory=ROOT/'app/static'),name='static')
    return api
