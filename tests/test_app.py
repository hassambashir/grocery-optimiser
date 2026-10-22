"""Integration tests: authenticated HTTP, actual solver, transactional stock."""
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import create_app


class HouseholdFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.url='sqlite:///'+str(Path(self.tmp.name)/'home.db')
        self.app=create_app(self.url,'test-password-123','test-session-secret-'*3,False)
        self.client=TestClient(self.app)
        self.headers={'X-Grocery-Request':'1'}
        self.assertEqual(self.post('/login',{'password':'test-password-123'}).status_code,200)

    def tearDown(self):
        self.client.close();self.app.state.engine.dispose();self.tmp.cleanup()

    def post(self,path,data):
        return self.client.post('/api'+path,json=data,headers=self.headers)

    def state(self):return self.client.get('/api/state').json()

    def stock(self,i,q,action='add',**extra):
        return self.post('/stock',dict(request_id=str(uuid4()),revision=self.state()['revision'],ingredient_id=i,quantity=q,action=action,**extra))

    def plan(self,days=1,required=None):
        r=self.post('/plans',{'days':days,'required_recipes':required or ['R034']})
        self.assertEqual(r.status_code,200,r.text);return r.json()

    def test_authentication_and_csrf(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertIn('Your kitchen',self.client.get('/').text)
        self.assertEqual(self.client.post('/api/logout',json={}).status_code,403)
        self.post('/logout',{})
        self.assertEqual(self.client.get('/api/state').status_code,401)
        self.assertEqual(self.post('/login',{'password':'wrong'}).status_code,401)

    def test_add_correct_discard_persistence(self):
        self.assertEqual(self.state()['inventory'],{})
        self.stock('long_grain_rice',200);self.stock('long_grain_rice',1000)
        self.assertEqual(self.state()['inventory']['long_grain_rice'],1200)
        self.stock('long_grain_rice',1000,'set')
        self.stock('long_grain_rice',100,'discard')
        self.assertEqual(self.state()['inventory']['long_grain_rice'],900)
        self.assertEqual(sum(e['changes'].get('long_grain_rice',0) for e in self.state()['events']),900)
        another=create_app(self.url,'test-password-123','test-session-secret-'*3,False)
        with TestClient(another) as c:
            c.post('/api/login',json={'password':'test-password-123'},headers=self.headers)
            self.assertEqual(c.get('/api/state').json()['inventory']['long_grain_rice'],900)
        another.state.engine.dispose()

    def test_duplicate_request_and_stale_correction(self):
        body=dict(request_id=str(uuid4()),revision=0,ingredient_id='cucumber',quantity=0.5,action='add')
        self.assertEqual(self.post('/stock',body).status_code,200)
        self.assertEqual(self.post('/stock',body).status_code,200)
        self.assertEqual(self.state()['inventory']['cucumber'],0.5)
        body['request_id']=str(uuid4());body['action']='set'
        self.assertEqual(self.post('/stock',body).status_code,409)

    def test_invalid_and_expired_stock(self):
        self.assertEqual(self.stock('nonsense',1).status_code,422)
        self.assertEqual(self.stock('cucumber',-1).status_code,422)
        self.stock('cucumber',1,expires_on='2020-01-01')
        self.assertNotIn('cucumber',self.state()['inventory'])
        self.assertEqual(len(self.state()['batches']),1)
        p=self.plan()
        self.assertTrue(any(x['ingredient_id']=='cucumber' for x,_,_ in p['result']['basket']))
        self.stock('cucumber',1,'discard')
        self.assertEqual(self.state()['batches'],[])

    def test_preferences_exclude_required_recipe(self):
        r=self.client.put('/api/preferences',headers=self.headers,json={'excluded_ingredients':['tuna'],'excluded_recipes':[],'avoid_previous_plan':False})
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.post('/plans',{'days':1,'required_recipes':['R034']}).status_code,422)
        r=self.post('/plans',{'days':1,'required_recipes':[]})
        self.assertEqual(r.status_code,200,r.text)
        self.assertFalse(any(x['ingredient_id']=='tuna' for x in r.json()['result']['consumption']))
        self.assertEqual(self.state()['inventory'],{})

    def test_complete_receipts_meals_and_next_plan(self):
        first=self.plan();pid=first['id'];r=first['result']
        self.assertEqual(self.state()['inventory'],{})
        packs={x['product_id']:n for x,n,_ in r['basket']}
        body={'request_id':str(uuid4()),'packs':packs}
        self.assertEqual(self.post(f'/plans/{pid}/receipts',body).status_code,200)
        opening=self.state()['inventory']
        self.assertEqual(self.post(f'/plans/{pid}/receipts',body).status_code,200)
        self.assertEqual(self.state()['inventory'],opening)
        self.assertEqual(self.post(f'/plans/{pid}/receipts',{'request_id':str(uuid4()),'packs':packs}).status_code,409)
        meal={'request_id':str(uuid4()),'cooked':['R034'],'skipped':[]}
        self.assertEqual(self.post(f'/plans/{pid}/meals',meal).status_code,200)
        self.assertEqual(self.post(f'/plans/{pid}/meals',meal).status_code,200)
        ending=self.state()['inventory']
        for i,q in r['ending_inventory'].items():self.assertAlmostEqual(ending.get(i,0),q,places=4)
        second=self.plan()
        self.assertEqual({i:q for i,q in second['result']['opening_inventory'].items() if q>0},ending)
        self.assertLess(second['result']['spend_gbp'],r['spend_gbp'])

    def test_missing_purchase_rolls_back_consumption(self):
        p=self.plan();pid=p['id'];packs={x['product_id']:n if x['ingredient_id']!='tuna' else 0 for x,n,_ in p['result']['basket']}
        self.post(f'/plans/{pid}/receipts',{'request_id':str(uuid4()),'packs':packs})
        before=self.state()
        r=self.post(f'/plans/{pid}/meals',{'request_id':str(uuid4()),'cooked':['R034'],'skipped':[]})
        self.assertEqual(r.status_code,409)
        self.assertEqual(self.state()['inventory'],before['inventory'])
        self.assertEqual(self.state()['plans'][0]['meal_status'],{})
        r=self.post(f'/plans/{pid}/meals',{'request_id':str(uuid4()),'cooked':[],'skipped':['R034']})
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.state()['inventory'],before['inventory'])

    def test_repetition_rule_uses_confirmed_plan(self):
        p=self.plan();pid=p['id']
        self.post(f'/plans/{pid}/receipts',{'request_id':str(uuid4()),'packs':{x['product_id']:n for x,n,_ in p['result']['basket']}})
        self.client.put('/api/preferences',headers=self.headers,json={'excluded_ingredients':[],'excluded_recipes':[],'avoid_previous_plan':True})
        self.assertEqual(self.post('/plans',{'days':1,'required_recipes':['R034']}).status_code,422)

    def test_seven_dinners_http_solver(self):
        p=self.plan(7,[]) # plan helper defaults required R034, still jointly chooses other six
        self.assertEqual(len(p['result']['recipes']),7)
        self.assertEqual(p['result']['status'],'Optimal')
        self.assertTrue(all(isinstance(n,int) for _,n,_ in p['result']['basket']))
        self.assertEqual(self.state()['inventory'],{})

    def test_abandon_draft_and_fractional_purchase_rejected(self):
        p=self.plan();pid=p['id']
        packs={x['product_id']:n for x,n,_ in p['result']['basket']}
        first=next(iter(packs));packs[first]=0.5
        self.assertEqual(self.post(f'/plans/{pid}/receipts',{'request_id':str(uuid4()),'packs':packs}).status_code,422)
        self.assertEqual(self.state()['inventory'],{})
        self.assertEqual(self.post(f'/plans/{pid}/abandon',{}).status_code,200)
        self.assertEqual(self.state()['plans'][0]['archived'],1)
        self.assertEqual(self.post(f'/plans/{pid}/meals',{'request_id':str(uuid4()),'cooked':['R034'],'skipped':[]}).status_code,409)
        self.assertEqual(self.state()['inventory'],{})
