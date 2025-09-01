#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Run.it Platform
Tests all endpoints including authentication, profile, contracts, tokens, and NFTs
"""

import requests
import sys
import json
from datetime import datetime
import time

class RunItPlatformTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
        self.created_resources = {
            "profile_id": None,
            "contract_id": None,
            "token_id": None,
            "nft_token_id": None,
            "nft_serial": None
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def test_health_check(self):
        """Test health check endpoint"""
        success, status_code, data = self.make_request('GET', '/api/health')
        details = f"Status: {status_code}"
        if success and data.get('status') == 'healthy':
            details += f" - MongoDB: {data.get('mongodb')}, Hedera: {data.get('hedera')}"
        self.log_test("Health Check", success, details)
        return success

    def test_user_registration(self):
        """Test user registration"""
        success, status_code, data = self.make_request(
            'POST', '/api/auth/register', 
            self.test_user_data, 
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            details = f"Status: {status_code} - Token received"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Unknown error')}"
        
        self.log_test("User Registration", success, details)
        return success

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "username": self.test_user_data["username"],
            "password": self.test_user_data["password"]
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/auth/login', 
            login_data, 
            expected_status=200
        )
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            details = f"Status: {status_code} - Login successful"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Login failed')}"
        
        self.log_test("User Login", success, details)
        return success

    def test_dashboard_access(self):
        """Test dashboard endpoint"""
        success, status_code, data = self.make_request('GET', '/api/dashboard')
        
        if success:
            stats = data.get('stats', {})
            user_info = data.get('user', {})
            details = f"Status: {status_code} - Stats: {stats}, User: {user_info.get('username')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Dashboard access failed')}"
        
        self.log_test("Dashboard Access", success, details)
        return success

    def test_profile_creation(self):
        """Test profile creation"""
        profile_data = {
            "first_name": "Test",
            "last_name": "User",
            "nickname": "testuser",
            "phone": "+1234567890",
            "nationality": "US",
            "role_code": "P",
            "interests": ["blockchain", "technology"]
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/profile', 
            profile_data, 
            expected_status=200
        )
        
        if success and data.get('status') == 'success':
            self.created_resources['profile_id'] = data.get('profile_id')
            details = f"Status: {status_code} - Profile ID: {data.get('profile_id')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Profile creation failed')}"
        
        self.log_test("Profile Creation", success, details)
        return success

    def test_profile_retrieval(self):
        """Test profile retrieval"""
        success, status_code, data = self.make_request('GET', '/api/profile')
        
        if success and data.get('first_name'):
            details = f"Status: {status_code} - Name: {data.get('first_name')} {data.get('last_name')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Profile retrieval failed')}"
        
        self.log_test("Profile Retrieval", success, details)
        return success

    def test_contract_deployment(self):
        """Test smart contract deployment"""
        # Simple contract bytecode (example)
        contract_data = {
            "contract_name": "TestContract",
            "bytecode": "608060405234801561001057600080fd5b50600436106100365760003560e01c8063893d20e81461003b578063a6f9dae114610059575b600080fd5b610043610075565b60405161005091906100a4565b60405180910390f35b610073600480360381019061006e91906100f0565b61009e565b005b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b8060008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff16146100fc57600080fd5b806000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055505050565b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b600061016782610142565b9050919050565b6101778161015c565b82525050565b6000602082019050610192600083018461016e565b92915050565b600080fd5b6101a68161015c565b81146101b157600080fd5b50565b6000813590506101c38161019d565b92915050565b6000602082840312156101df576101de610198565b5b60006101ed848285016101b4565b9150509291505056fea2646970667358221220"
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/contracts/deploy', 
            contract_data, 
            expected_status=200
        )
        
        if success and data.get('status') == 'success':
            self.created_resources['contract_id'] = data.get('contract_id')
            details = f"Status: {status_code} - Contract ID: {data.get('contract_id')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Contract deployment failed')}"
        
        self.log_test("Contract Deployment", success, details)
        return success

    def test_contracts_list(self):
        """Test contracts listing"""
        success, status_code, data = self.make_request('GET', '/api/contracts')
        
        if success and isinstance(data, list):
            details = f"Status: {status_code} - Found {len(data)} contracts"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Contracts listing failed')}"
        
        self.log_test("Contracts Listing", success, details)
        return success

    def test_fungible_token_creation(self):
        """Test fungible token creation"""
        token_data = {
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 2,
            "initial_supply": 1000,
            "token_type": "fungible"
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/tokens/create', 
            token_data, 
            expected_status=200
        )
        
        if success and data.get('status') == 'success':
            self.created_resources['token_id'] = data.get('token_id')
            details = f"Status: {status_code} - Token ID: {data.get('token_id')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Token creation failed')}"
        
        self.log_test("Fungible Token Creation", success, details)
        return success

    def test_nft_collection_creation(self):
        """Test NFT collection creation"""
        nft_data = {
            "name": "Test NFT Collection",
            "symbol": "TNFT",
            "initial_supply": 100,
            "token_type": "nft"
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/tokens/create', 
            nft_data, 
            expected_status=200
        )
        
        if success and data.get('status') == 'success':
            self.created_resources['nft_token_id'] = data.get('token_id')
            details = f"Status: {status_code} - NFT Collection ID: {data.get('token_id')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'NFT collection creation failed')}"
        
        self.log_test("NFT Collection Creation", success, details)
        return success

    def test_tokens_list(self):
        """Test tokens listing"""
        success, status_code, data = self.make_request('GET', '/api/tokens')
        
        if success and isinstance(data, list):
            details = f"Status: {status_code} - Found {len(data)} tokens"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Tokens listing failed')}"
        
        self.log_test("Tokens Listing", success, details)
        return success

    def test_nft_minting(self):
        """Test NFT minting"""
        if not self.created_resources['nft_token_id']:
            self.log_test("NFT Minting", False, "No NFT collection available")
            return False
        
        nft_data = {
            "token_id": self.created_resources['nft_token_id'],
            "metadata": {
                "name": "Test NFT #1",
                "description": "A test NFT for platform testing",
                "image": "https://example.com/test-nft.png",
                "attributes": [
                    {"trait_type": "Color", "value": "Blue"},
                    {"trait_type": "Rarity", "value": "Common"}
                ]
            }
        }
        
        success, status_code, data = self.make_request(
            'POST', '/api/nfts/mint', 
            nft_data, 
            expected_status=200
        )
        
        if success and data.get('status') == 'success':
            self.created_resources['nft_serial'] = data.get('serial_number')
            details = f"Status: {status_code} - Serial: {data.get('serial_number')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'NFT minting failed')}"
        
        self.log_test("NFT Minting", success, details)
        return success

    def test_nfts_list(self):
        """Test NFTs listing"""
        success, status_code, data = self.make_request('GET', '/api/nfts')
        
        if success and isinstance(data, list):
            details = f"Status: {status_code} - Found {len(data)} NFTs"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'NFTs listing failed')}"
        
        self.log_test("NFTs Listing", success, details)
        return success

    def test_account_balance(self):
        """Test account balance query"""
        success, status_code, data = self.make_request('GET', '/api/account/balance')
        
        if success and 'hbar_balance' in data:
            details = f"Status: {status_code} - HBAR: {data.get('hbar_balance')}"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Balance query failed')}"
        
        self.log_test("Account Balance Query", success, details)
        return success

    def test_transactions_list(self):
        """Test transactions listing"""
        success, status_code, data = self.make_request('GET', '/api/transactions')
        
        if success and isinstance(data, list):
            details = f"Status: {status_code} - Found {len(data)} transactions"
        else:
            details = f"Status: {status_code} - {data.get('detail', 'Transactions listing failed')}"
        
        self.log_test("Transactions Listing", success, details)
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Run.it Platform Backend API Tests")
        print("=" * 60)
        
        # Basic connectivity and health
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication flow
        if not self.test_user_registration():
            print("❌ User registration failed - stopping tests")
            return False
        
        if not self.test_user_login():
            print("❌ User login failed - stopping tests")
            return False
        
        # Dashboard and profile
        self.test_dashboard_access()
        self.test_profile_creation()
        self.test_profile_retrieval()
        
        # Smart contracts
        self.test_contract_deployment()
        self.test_contracts_list()
        
        # Tokens and NFTs
        self.test_fungible_token_creation()
        self.test_nft_collection_creation()
        self.test_tokens_list()
        self.test_nft_minting()
        self.test_nfts_list()
        
        # Account and transactions
        self.test_account_balance()
        self.test_transactions_list()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed")
            return False

def main():
    """Main test execution"""
    tester = RunItPlatformTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())