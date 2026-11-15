import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import create_app


class SupportApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'support.sqlite'
        self.client=TestClient(create_app(self.db))
    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()
    def test_health_cases_and_order(self):
        self.assertEqual(self.client.get('/api/health').json()['storage'],'sqlite')
        self.assertEqual(len(self.client.get('/api/cases').json()['cases']),3)
        self.assertEqual(self.client.get('/api/order?id=ns-1042').json()['status'],'Delivered')
        self.assertEqual(self.client.get('/api/order?id=NS-9999').status_code,404)
    def test_documents_search_persist_and_delete(self):
        self.assertEqual(self.client.post('/api/documents',json={'name':'warranty.txt','text':'Warranty coverage lasts two years.'}).status_code,201)
        self.assertEqual(self.client.post('/api/documents',json={'name':'WARRANTY.TXT','text':'duplicate'}).status_code,409)
        response=self.client.post('/api/answer',json={'question':'warranty coverage'}).json()
        self.assertEqual(response['source'],'warranty.txt')
        self.assertIn('two years',response['answer'])
        again=TestClient(create_app(self.db))
        self.assertEqual(len(again.get('/api/documents').json()['documents']),1)
        again.close()
        self.assertEqual(self.client.post('/api/documents/delete',json={'name':'warranty.txt'}).status_code,200)
        self.assertEqual(self.client.post('/api/answer',json={'question':'warranty coverage'}).json()['mode'],'no_match')
    def test_approval_messages_review_and_reset(self):
        self.assertEqual(self.client.post('/api/messages',json={'caseId':'CS-102','who':'customer','message':'Please check'}).status_code,200)
        self.assertEqual(self.client.post('/api/approval',json={'decision':'Approved'}).status_code,200)
        self.assertEqual(self.client.post('/api/approval',json={'decision':'Rejected'}).status_code,409)
        r=self.client.post('/api/escalations',json={'caseId':'CS-102','summary':'Please check'})
        self.assertEqual(r.status_code,201)
        ident=r.json()['id']
        self.assertEqual(self.client.post('/api/escalations',json={'caseId':'CS-102','summary':'Again'}).status_code,409)
        again=TestClient(create_app(self.db))
        self.assertEqual(again.get('/api/state').json()['approval'],'Approved')
        self.assertEqual(again.get('/api/state').json()['logs']['CS-102'][0][1],'Please check')
        self.assertEqual(again.post('/api/escalations/resolve',json={'id':ident}).status_code,200)
        self.assertEqual(again.post('/api/escalations/resolve',json={'id':ident}).status_code,409)
        self.assertEqual(again.post('/api/reset',json={}).status_code,200)
        state=again.get('/api/state').json()
        self.assertEqual((state['approval'],state['logs'],state['documents'],state['escalations']),('pending',{},[],[]))
        again.close()
    def test_input_and_origin_validation(self):
        self.assertIn(self.client.post('/api/messages',json={'caseId':'x','who':'customer','message':'hi'}).status_code,(400,422))
        self.assertEqual(self.client.post('/api/documents',json={'name':'x.pdf','text':'x'}).status_code,400)
        self.assertEqual(self.client.post('/api/reset',json={},headers={'origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.get('/api/health').headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/api/answer',json={'question':'Can speakers connect wirelessly?'}).json()['mode'],'no_match')
    def test_frontend_served(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertIn('Resolve AI',response.text)

if __name__ == '__main__': unittest.main()
