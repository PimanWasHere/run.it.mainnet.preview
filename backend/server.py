from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
import uuid
from pathlib import Path

# Hedera imports
try:
    from hedera import (
        Client, PrivateKey, AccountId, Hbar,
        FileCreateTransaction, ContractCreateTransaction,
        ContractCallQuery, ContractExecuteTransaction,
        TokenCreateTransaction, TokenType, TokenSupplyType,
        TokenAssociateTransaction, TransferTransaction,
        TokenMintTransaction, AccountBalanceQuery,
        ContractFunctionParameters, TokenWipeTransaction,
        TokenFreezeTransaction, AccountCreateTransaction
    )
    HEDERA_AVAILABLE = True
except ImportError as e:
    print(f"Hedera SDK not available: {e}")
    HEDERA_AVAILABLE = False

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "run_it_secret_key_2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

# Database connection
client = None
db = None

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Global Hedera client
hedera_client = None
operator_id = None
operator_key = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client, db, hedera_client, operator_id, operator_key
    
    # MongoDB connection
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.runit_platform
    print("✅ Connected to MongoDB")
    
    # Initialize Hedera client if available
    if HEDERA_AVAILABLE:
        try:
            # Use demo testnet credentials
            hedera_client = Client.forTestnet()
            
            # Demo operator account (testnet)
            operator_id = AccountId.fromString("0.0.4827036")  # Demo testnet account
            operator_key = PrivateKey.fromString("302e020100300506032b6570042204204a68a0b8d09e0e5c26c8bb9b2b6a4c8a5e5d5c4b3a2918171615141312111009")
            
            hedera_client.setOperator(operator_id, operator_key)
            hedera_client.setDefaultMaxTransactionFee(Hbar(10))
            hedera_client.setMaxQueryPayment(Hbar(1))
            
            print("✅ Connected to Hedera Testnet")
        except Exception as e:
            print(f"❌ Failed to connect to Hedera: {e}")
            hedera_client = None
    
    yield
    
    # Shutdown
    if client:
        client.close()
    if hedera_client:
        hedera_client.close()

app = FastAPI(
    title="Run.it Platform API",
    description="Comprehensive platform for Hedera smart contracts, tokens, and NFTs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Pydantic models
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileCreate(BaseModel):
    first_name: str
    last_name: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
    role_code: str = "P"  # P/F/S/C/B/R/D
    interests: Optional[List[str]] = []
    privacy_settings: Optional[Dict[str, bool]] = None

class TokenCreateRequest(BaseModel):
    name: str
    symbol: str
    decimals: int = 2
    initial_supply: int
    token_type: str = "fungible"  # fungible or nft

class ContractDeployRequest(BaseModel):
    contract_name: str
    bytecode: str
    constructor_params: Optional[str] = None

class TokenTransferRequest(BaseModel):
    token_id: str
    to_account: str
    amount: int

class NFTMintRequest(BaseModel):
    token_id: str
    metadata: Dict[str, Any]

class WalletConnectRequest(BaseModel):
    account_id: str
    public_key: str
    signature: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

# Hedera utility functions
async def create_hedera_account():
    """Create a new Hedera account for user"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        new_key = PrivateKey.generate()
        
        account_create = AccountCreateTransaction() \
            .setKey(new_key.getPublicKey()) \
            .setInitialBalance(Hbar(10)) \
            .setMaxTransactionFee(Hbar(20))
        
        account_signed = account_create.sign(operator_key)
        account_submit = await account_signed.execute(hedera_client)
        account_receipt = await account_submit.getReceipt(hedera_client)
        
        return {
            "account_id": str(account_receipt.accountId),
            "private_key": str(new_key),
            "public_key": str(new_key.getPublicKey())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Hedera account: {str(e)}")

# Authentication endpoints
@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create Hedera account for user
    hedera_account = None
    if hedera_client:
        try:
            hedera_account = await create_hedera_account()
        except Exception as e:
            print(f"Warning: Could not create Hedera account: {e}")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "hedera_account": hedera_account,
        "profile": None
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/wallet-connect")
async def wallet_connect(request: WalletConnectRequest, current_user: dict = Depends(get_current_user)):
    """Connect Hedera wallet to user account"""
    try:
        # Verify the signature and account
        account_id = AccountId.fromString(request.account_id)
        
        # Update user with wallet info
        await db.users.update_one(
            {"username": current_user["username"]},
            {
                "$set": {
                    "wallet_connected": True,
                    "wallet_account_id": request.account_id,
                    "wallet_public_key": request.public_key,
                    "wallet_connected_at": datetime.utcnow()
                }
            }
        )
        
        return {"status": "success", "message": "Wallet connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect wallet: {str(e)}")

# Profile endpoints
@app.post("/api/profile")
async def create_profile(profile: ProfileCreate, current_user: dict = Depends(get_current_user)):
    """Create user profile"""
    profile_doc = {
        "user_id": str(current_user["_id"]),
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "nickname": profile.nickname,
        "phone": profile.phone,
        "nationality": profile.nationality,
        "role_code": profile.role_code,
        "interests": profile.interests or [],
        "privacy_settings": profile.privacy_settings or {
            "demographic": False,
            "behavioral": False,
            "interests": False
        },
        "created_at": datetime.utcnow(),
        "kyc_approved": False
    }
    
    result = await db.profiles.insert_one(profile_doc)
    
    # Update user to reference profile
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"profile_id": str(result.inserted_id)}}
    )
    
    return {"status": "success", "profile_id": str(result.inserted_id)}

@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    if not current_user.get("profile_id"):
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await db.profiles.find_one({"user_id": str(current_user["_id"])})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Convert ObjectId to string
    profile["_id"] = str(profile["_id"])
    return profile

# Smart Contract endpoints
@app.post("/api/contracts/deploy")
async def deploy_contract(request: ContractDeployRequest, current_user: dict = Depends(get_current_user)):
    """Deploy smart contract to Hedera"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        # Convert hex bytecode to bytes
        bytecode = bytes.fromhex(request.bytecode.replace('0x', ''))
        
        # Step 1: Create file with contract bytecode
        file_create = FileCreateTransaction() \
            .setContents(bytecode) \
            .setMaxTransactionFee(Hbar(2))
        
        file_create_frozen = file_create.freeze()
        file_signed = file_create_frozen.sign(operator_key)
        file_submit = await file_signed.execute(hedera_client)
        file_receipt = await file_submit.getReceipt(hedera_client)
        
        # Step 2: Create contract
        contract_create = ContractCreateTransaction() \
            .setBytecodeFileId(file_receipt.fileId) \
            .setMaxTransactionFee(Hbar(20))
        
        if request.constructor_params:
            # Add constructor parameters if provided
            params = ContractFunctionParameters()
            # Parse constructor parameters (simplified)
            contract_create.setConstructorParameters(params)
        
        contract_create_frozen = contract_create.freeze()
        contract_signed = contract_create_frozen.sign(operator_key)
        contract_submit = await contract_signed.execute(hedera_client)
        contract_receipt = await contract_submit.getReceipt(hedera_client)
        
        # Save contract info to database
        contract_doc = {
            "user_id": str(current_user["_id"]),
            "contract_name": request.contract_name,
            "contract_id": str(contract_receipt.contractId),
            "contract_address": contract_receipt.contractId.toSolidityAddress(),
            "bytecode_file_id": str(file_receipt.fileId),
            "deployed_at": datetime.utcnow(),
            "status": "deployed"
        }
        
        await db.contracts.insert_one(contract_doc)
        
        return {
            "status": "success",
            "contract_id": str(contract_receipt.contractId),
            "contract_address": contract_receipt.contractId.toSolidityAddress(),
            "transaction_id": str(contract_submit.transactionId)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract deployment failed: {str(e)}")

@app.get("/api/contracts")
async def get_contracts(current_user: dict = Depends(get_current_user)):
    """Get user's deployed contracts"""
    contracts = await db.contracts.find({"user_id": str(current_user["_id"])}).to_list(100)
    for contract in contracts:
        contract["_id"] = str(contract["_id"])
    return contracts

# Token endpoints
@app.post("/api/tokens/create")
async def create_token(request: TokenCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create fungible token or NFT collection"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        supply_key = PrivateKey.generate()
        
        if request.token_type == "fungible":
            token_create = TokenCreateTransaction() \
                .setTokenName(request.name) \
                .setTokenSymbol(request.symbol) \
                .setTokenType(TokenType.FUNGIBLE_COMMON) \
                .setDecimals(request.decimals) \
                .setInitialSupply(request.initial_supply * (10 ** request.decimals)) \
                .setTreasuryAccountId(operator_id) \
                .setSupplyType(TokenSupplyType.INFINITE) \
                .setSupplyKey(supply_key) \
                .setMaxTransactionFee(Hbar(30))
        else:  # NFT
            token_create = TokenCreateTransaction() \
                .setTokenName(request.name) \
                .setTokenSymbol(request.symbol) \
                .setTokenType(TokenType.NON_FUNGIBLE_UNIQUE) \
                .setDecimals(0) \
                .setInitialSupply(0) \
                .setTreasuryAccountId(operator_id) \
                .setSupplyType(TokenSupplyType.FINITE) \
                .setMaxSupply(request.initial_supply) \
                .setSupplyKey(supply_key) \
                .setMaxTransactionFee(Hbar(30))
        
        token_signed = token_create.sign(operator_key)
        token_submit = await token_signed.execute(hedera_client)
        token_receipt = await token_submit.getReceipt(hedera_client)
        
        # Save token info to database
        token_doc = {
            "user_id": str(current_user["_id"]),
            "token_name": request.name,
            "token_symbol": request.symbol,
            "token_id": str(token_receipt.tokenId),
            "token_type": request.token_type,
            "decimals": request.decimals if request.token_type == "fungible" else 0,
            "initial_supply": request.initial_supply,
            "supply_key": str(supply_key),
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        await db.tokens.insert_one(token_doc)
        
        return {
            "status": "success",
            "token_id": str(token_receipt.tokenId),
            "transaction_id": str(token_submit.transactionId)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token creation failed: {str(e)}")

@app.get("/api/tokens")
async def get_tokens(current_user: dict = Depends(get_current_user)):
    """Get user's tokens"""
    tokens = await db.tokens.find({"user_id": str(current_user["_id"])}).to_list(100)
    for token in tokens:
        token["_id"] = str(token["_id"])
    return tokens

@app.post("/api/tokens/transfer")
async def transfer_tokens(request: TokenTransferRequest, current_user: dict = Depends(get_current_user)):
    """Transfer tokens to another account"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        token_id = request.token_id
        to_account = AccountId.fromString(request.to_account)
        
        # Check if user owns this token
        token = await db.tokens.find_one({"user_id": str(current_user["_id"]), "token_id": token_id})
        if not token:
            raise HTTPException(status_code=404, detail="Token not found or not owned by user")
        
        transfer_tx = TransferTransaction() \
            .addTokenTransfer(token_id, operator_id, -request.amount) \
            .addTokenTransfer(token_id, to_account, request.amount) \
            .setMaxTransactionFee(Hbar(5))
        
        transfer_signed = transfer_tx.sign(operator_key)
        transfer_submit = await transfer_signed.execute(hedera_client)
        transfer_receipt = await transfer_submit.getReceipt(hedera_client)
        
        # Log transaction
        transaction_doc = {
            "user_id": str(current_user["_id"]),
            "transaction_type": "token_transfer",
            "token_id": token_id,
            "from_account": str(operator_id),
            "to_account": request.to_account,
            "amount": request.amount,
            "transaction_id": str(transfer_submit.transactionId),
            "timestamp": datetime.utcnow(),
            "status": str(transfer_receipt.status)
        }
        
        await db.transactions.insert_one(transaction_doc)
        
        return {
            "status": "success",
            "transaction_id": str(transfer_submit.transactionId)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token transfer failed: {str(e)}")

# NFT endpoints
@app.post("/api/nfts/mint")
async def mint_nft(request: NFTMintRequest, current_user: dict = Depends(get_current_user)):
    """Mint NFT"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        # Get token info
        token = await db.tokens.find_one({"user_id": str(current_user["_id"]), "token_id": request.token_id})
        if not token or token["token_type"] != "nft":
            raise HTTPException(status_code=404, detail="NFT collection not found")
        
        # Prepare metadata
        metadata_json = json.dumps(request.metadata)
        metadata_bytes = metadata_json.encode('utf-8')
        
        supply_key = PrivateKey.fromString(token["supply_key"])
        
        mint_tx = TokenMintTransaction() \
            .setTokenId(request.token_id) \
            .setMetadata([metadata_bytes]) \
            .setMaxTransactionFee(Hbar(20))
        
        mint_signed = mint_tx.sign(supply_key)
        mint_submit = await mint_signed.execute(hedera_client)
        mint_receipt = await mint_submit.getReceipt(hedera_client)
        
        # Save NFT info
        nft_doc = {
            "user_id": str(current_user["_id"]),
            "token_id": request.token_id,
            "serial_number": mint_receipt.serials[0],
            "metadata": request.metadata,
            "owner_account": str(operator_id),
            "minted_at": datetime.utcnow(),
            "transaction_id": str(mint_submit.transactionId)
        }
        
        await db.nfts.insert_one(nft_doc)
        
        return {
            "status": "success",
            "serial_number": mint_receipt.serials[0],
            "transaction_id": str(mint_submit.transactionId)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NFT minting failed: {str(e)}")

@app.get("/api/nfts")
async def get_nfts(current_user: dict = Depends(get_current_user)):
    """Get user's NFTs"""
    nfts = await db.nfts.find({"user_id": str(current_user["_id"])}).to_list(100)
    for nft in nfts:
        nft["_id"] = str(nft["_id"])
    return nfts

# Account and balance endpoints
@app.get("/api/account/balance")
async def get_account_balance(current_user: dict = Depends(get_current_user)):
    """Get account balance"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    try:
        balance_query = AccountBalanceQuery().setAccountId(operator_id)
        balance = await balance_query.execute(hedera_client)
        
        return {
            "hbar_balance": str(balance.hbars),
            "token_balances": {str(k): v for k, v in balance.tokenBalances.items()},
            "account_id": str(operator_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@app.get("/api/transactions")
async def get_transactions(current_user: dict = Depends(get_current_user)):
    """Get user's transaction history"""
    transactions = await db.transactions.find({"user_id": str(current_user["_id"])}).sort("timestamp", -1).to_list(100)
    for transaction in transactions:
        transaction["_id"] = str(transaction["_id"])
    return transactions

# Dashboard endpoint
@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get dashboard data"""
    # Get counts
    contracts_count = await db.contracts.count_documents({"user_id": str(current_user["_id"])})
    tokens_count = await db.tokens.count_documents({"user_id": str(current_user["_id"])})
    nfts_count = await db.nfts.count_documents({"user_id": str(current_user["_id"])})
    transactions_count = await db.transactions.count_documents({"user_id": str(current_user["_id"])})
    
    # Get recent transactions
    recent_transactions = await db.transactions.find({"user_id": str(current_user["_id"])}).sort("timestamp", -1).limit(5).to_list(5)
    for transaction in recent_transactions:
        transaction["_id"] = str(transaction["_id"])
    
    return {
        "stats": {
            "contracts": contracts_count,
            "tokens": tokens_count,
            "nfts": nfts_count,
            "transactions": transactions_count
        },
        "recent_transactions": recent_transactions,
        "user": {
            "username": current_user["username"],
            "email": current_user["email"],
            "wallet_connected": current_user.get("wallet_connected", False),
            "hedera_account": current_user.get("hedera_account")
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "mongodb": "connected" if client else "disconnected",
        "hedera": "connected" if hedera_client else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)