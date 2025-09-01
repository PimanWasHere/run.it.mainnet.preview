#!/usr/bin/env python3
"""
Setup Hedera credentials from mnemonic phrase
"""

import os
import sys
from hedera import Mnemonic, Client, AccountId, AccountBalanceQuery

def setup_credentials():
    """Convert mnemonic to proper credentials and test connection"""
    
    # User provided credentials
    account_id_str = "0.0.2181027"  # Removing the suffix for now
    mnemonic_phrase = "good siege egg plunge egg tongue parent beach apart notice huge rib lazy patient code shallow hotel either rug diary mean noodle voice marble"
    
    print("🔧 Setting up Hedera testnet credentials...")
    print(f"Account ID: {account_id_str}")
    print(f"Mnemonic: {mnemonic_phrase}")
    
    try:
        # Convert mnemonic to private key
        mnemonic = Mnemonic.fromString(mnemonic_phrase)
        private_key = mnemonic.toStandardEd25519PrivateKey("", 0)
        
        print(f"✅ Private key generated: {str(private_key)}")
        
        # Test connection
        client = Client.forTestnet()
        account_id = AccountId.fromString(account_id_str)
        
        client.setOperator(account_id, private_key)
        
        print("🧪 Testing connection...")
        
        # Test balance query
        balance_query = AccountBalanceQuery().setAccountId(account_id)
        balance = balance_query.execute(client)
        
        print(f"✅ Connection successful!")
        print(f"Account balance: {balance.hbars.toString()}")
        
        # Update environment file
        env_content = f"""MONGO_URL=mongodb://localhost:27017
SECRET_KEY=run_it_platform_secret_key_2024_hedera_integration
HEDERA_NETWORK=testnet
MY_ACCOUNT_ID={account_id_str}
MY_PRIVATE_KEY={str(private_key)}
"""
        
        with open('/app/backend/.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Updated /app/backend/.env with new credentials")
        
        return True, account_id_str, str(private_key)
        
    except Exception as e:
        print(f"❌ Error setting up credentials: {str(e)}")
        return False, None, None

if __name__ == "__main__":
    success, account_id, private_key = setup_credentials()
    if success:
        print("\n🎉 Hedera credentials setup completed successfully!")
        print("You can now restart the backend to use the new credentials.")
    else:
        print("\n💥 Failed to setup credentials. Please check the logs above.")
        sys.exit(1)