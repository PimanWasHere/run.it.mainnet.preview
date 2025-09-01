#!/usr/bin/env python3
"""
Setup Hedera MAINNET credentials - REAL MONEY TRANSACTIONS
"""

import os
import sys
from hedera import Mnemonic, Client, AccountId, AccountBalanceQuery

def setup_mainnet_credentials():
    """Convert mnemonic to mainnet credentials and test connection"""
    
    # MAINNET credentials - REAL MONEY
    account_id_str = "0.0.2181027-gpfpb"  # User provided mainnet account with checksum
    mnemonic_phrase = "good siege egg plunge egg tongue parent beach apart notice huge rib lazy patient code shallow hotel either rug diary mean noodle voice marble"
    
    print("🚨 SETTING UP HEDERA **MAINNET** CREDENTIALS - REAL MONEY TRANSACTIONS")
    print("=" * 80)
    print(f"⚠️  WARNING: ALL TRANSACTIONS WILL COST REAL HBAR (REAL MONEY)")
    print(f"⚠️  Contract deployment: ~$5-20 USD")
    print(f"⚠️  Token creation: ~$1-5 USD")
    print(f"⚠️  Each transaction: ~$0.01-0.10 USD")
    print("=" * 80)
    print(f"Mainnet Account ID: {account_id_str}")
    print(f"Mnemonic: {mnemonic_phrase}")
    
    try:
        # Convert mnemonic to private key
        mnemonic = Mnemonic.fromString(mnemonic_phrase)
        private_key = mnemonic.toStandardEd25519PrivateKey("", 0)
        
        # Get the DER string representation
        private_key_der = private_key.toStringDER()
        print(f"✅ Private key generated: {private_key_der}")
        
        # Test MAINNET connection
        print("🧪 Testing MAINNET connection...")
        client = Client.forMainnet()  # MAINNET CLIENT
        account_id = AccountId.fromString(account_id_str)
        
        client.setOperator(account_id, private_key)
        
        # Test balance query
        balance_query = AccountBalanceQuery().setAccountId(account_id)
        balance = balance_query.execute(client)
        
        print(f"✅ MAINNET connection successful!")
        print(f"🏦 Account balance: {balance.hbars.toString()}")
        print(f"💰 This is REAL HBAR with monetary value!")
        
        # Create mainnet environment file
        env_content = f"""MONGO_URL=mongodb://localhost:27017
SECRET_KEY=run_it_platform_mainnet_production_key_2024
HEDERA_NETWORK=mainnet
MY_ACCOUNT_ID={account_id_str}
MY_PRIVATE_KEY={private_key_der}
MAINNET_MODE=true
COST_WARNING_ENABLED=true
"""
        
        with open('/app/backend/.env.mainnet', 'w') as f:
            f.write(env_content)
        
        print("✅ Created /app/backend/.env.mainnet with MAINNET credentials")
        
        # Also create a testnet backup
        testnet_env = f"""MONGO_URL=mongodb://localhost:27017
SECRET_KEY=run_it_platform_testnet_development_key_2024
HEDERA_NETWORK=testnet
MY_ACCOUNT_ID={account_id_str}
MY_PRIVATE_KEY={private_key_der}
MAINNET_MODE=false
COST_WARNING_ENABLED=false
"""
        
        with open('/app/backend/.env.testnet', 'w') as f:
            f.write(testnet_env)
        
        print("✅ Created /app/backend/.env.testnet as backup")
        
        return True, account_id_str, private_key_der, str(balance.hbars)
        
    except Exception as e:
        print(f"❌ Error setting up MAINNET credentials: {str(e)}")
        return False, None, None, None

if __name__ == "__main__":
    print("🚨 MAINNET SETUP - PROCEEDING AS REQUESTED")
    
    success, account_id, private_key, balance = setup_mainnet_credentials()
    if success:
        print("\n🎉 MAINNET credentials setup completed successfully!")
        print(f"💰 Account balance: {balance}")
        print("\n⚠️  IMPORTANT REMINDERS:")
        print("- All transactions will cost real HBAR")
        print("- Test on testnet first before using mainnet features")
        print("- Use /app/backend/.env.testnet for development")
        print("- Use /app/backend/.env.mainnet for production")
        print("\nRestart the backend to use the new credentials.")
    else:
        print("\n💥 Failed to setup MAINNET credentials. Please check the logs above.")
        sys.exit(1)