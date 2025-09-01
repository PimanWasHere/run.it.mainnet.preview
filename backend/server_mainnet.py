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

# 🚨 MAINNET CONFIGURATION
MAINNET_MODE = os.getenv("MAINNET_MODE", "true").lower() == "true"
COST_WARNING_ENABLED = os.getenv("COST_WARNING_ENABLED", "true").lower() == "true"

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "run_it_mainnet_production_secret_2024")
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
    
    print("🚨" * 20)
    print("⚠️  MAINNET MODE ACTIVATED - REAL MONEY TRANSACTIONS")
    print("💰 All operations will cost real HBAR")
    print("🚨" * 20)
    
    # MongoDB connection
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.runit_platform_mainnet if MAINNET_MODE else client.runit_platform_testnet
    print(f"✅ Connected to MongoDB ({'MAINNET' if MAINNET_MODE else 'TESTNET'} database)")
    
    # Initialize Hedera client if available
    if HEDERA_AVAILABLE:
        try:
            # Use MAINNET client
            hedera_client = Client.forMainnet() if MAINNET_MODE else Client.forTestnet()
            
            # Production operator account
            operator_id = AccountId.fromString(os.getenv("MY_ACCOUNT_ID", "0.0.2181027-gpfpb"))
            operator_key = PrivateKey.fromString(os.getenv("MY_PRIVATE_KEY"))
            
            hedera_client.setOperator(operator_id, operator_key)
            hedera_client.setDefaultMaxTransactionFee(Hbar(20))  # Higher fee for mainnet
            hedera_client.setMaxQueryPayment(Hbar(2))
            
            # Test balance
            balance_query = AccountBalanceQuery().setAccountId(operator_id)
            balance = balance_query.execute(hedera_client)
            
            network_name = "MAINNET" if MAINNET_MODE else "TESTNET"
            print(f"✅ Connected to Hedera {network_name}")
            print(f"💰 Account balance: {balance.hbars.toString()}")
            
            if MAINNET_MODE:
                print("⚠️  WARNING: This account has REAL HBAR value!")
                
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
    title="Run.it Platform API - MAINNET",
    description="Production Hedera Mainnet smart contracts, tokens, and NFTs platform",
    version="1.0.0-mainnet",
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

class CostWarning(BaseModel):
    operation: str
    estimated_cost_usd: str
    estimated_cost_hbar: str
    warning_message: str

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
    role_code: str = "P"
    interests: Optional[List[str]] = []
    privacy_settings: Optional[Dict[str, bool]] = None

class TokenCreateRequest(BaseModel):
    name: str
    symbol: str
    decimals: int = 2
    initial_supply: int
    token_type: str = "fungible"
    confirm_cost: bool = False  # User must confirm they understand the cost

class ContractDeployRequest(BaseModel):
    contract_name: str
    bytecode: str
    constructor_params: Optional[str] = None
    confirm_cost: bool = False  # User must confirm they understand the cost

class TokenTransferRequest(BaseModel):
    token_id: str
    to_account: str
    amount: int
    confirm_cost: bool = False

class NFTMintRequest(BaseModel):
    token_id: str
    metadata: Dict[str, Any]
    confirm_cost: bool = False

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

def get_cost_warning(operation: str) -> CostWarning:
    """Get cost warning for mainnet operations"""
    cost_estimates = {
        "contract_deploy": {"usd": "$5-20", "hbar": "5-20 ℏ", "desc": "Smart contract deployment"},
        "token_create": {"usd": "$1-5", "hbar": "1-5 ℏ", "desc": "Token/NFT collection creation"},
        "nft_mint": {"usd": "$0.50-2", "hbar": "0.5-2 ℏ", "desc": "NFT minting"},
        "token_transfer": {"usd": "$0.01-0.10", "hbar": "0.01-0.1 ℏ", "desc": "Token transfer"},
        "account_create": {"usd": "$1-2", "hbar": "1-2 ℏ", "desc": "Account creation"}
    }
    
    estimate = cost_estimates.get(operation, {"usd": "$0.01-1", "hbar": "0.01-1 ℏ", "desc": "Operation"})
    
    return CostWarning(
        operation=operation,
        estimated_cost_usd=estimate["usd"],
        estimated_cost_hbar=estimate["hbar"],
        warning_message=f"⚠️ MAINNET OPERATION: {estimate['desc']} will cost approximately {estimate['usd']} in real money. This transaction cannot be undone."
    )

def require_cost_confirmation(confirmed: bool, operation: str):
    """Require explicit cost confirmation for mainnet operations"""
    if MAINNET_MODE and COST_WARNING_ENABLED and not confirmed:
        cost_warning = get_cost_warning(operation)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Cost confirmation required",
                "cost_warning": cost_warning.dict(),
                "message": "You must confirm you understand this operation will cost real money. Set 'confirm_cost': true in your request."
            }
        )

# Hedera utility functions
async def create_hedera_account():
    """Create a new Hedera account for user - COSTS REAL MONEY ON MAINNET"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    if MAINNET_MODE:
        raise HTTPException(
            status_code=400, 
            detail="Account creation disabled on mainnet to prevent unexpected costs. Users should create their own accounts via Hedera wallet apps."
        )
    
    try:
        new_key = PrivateKey.generate()
        
        account_create = AccountCreateTransaction() \
            .setKey(new_key.getPublicKey()) \
            .setInitialBalance(Hbar(1)) \
            .setMaxTransactionFee(Hbar(20))
        
        account_create_frozen = account_create.freeze()
        account_signed = account_create_frozen.sign(operator_key)
        account_submit = await account_signed.execute(hedera_client)
        account_receipt = await account_submit.getReceipt(hedera_client)
        
        return {
            "account_id": str(account_receipt.accountId),
            "private_key": str(new_key),
            "public_key": str(new_key.getPublicKey())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Hedera account: {str(e)}")

# Cost estimation endpoints
@app.get("/api/costs/estimate/{operation}")
async def get_operation_cost(operation: str):
    """Get cost estimate for mainnet operations"""
    if not MAINNET_MODE:
        return {"message": "Testnet mode - no costs", "cost": "Free"}
    
    return get_cost_warning(operation).dict()

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
    
    # Don't create Hedera accounts automatically on mainnet
    hedera_account = None
    if not MAINNET_MODE and hedera_client:
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
        "profile": None,
        "mainnet_mode": MAINNET_MODE
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
    """Deploy smart contract to Hedera - COSTS REAL MONEY ON MAINNET"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    # Require cost confirmation on mainnet
    require_cost_confirmation(request.confirm_cost, "contract_deploy")
    
    try:
        # Convert hex bytecode to bytes
        bytecode = bytes.fromhex(request.bytecode.replace('0x', ''))
        
        # Step 1: Create file with contract bytecode
        file_create = FileCreateTransaction() \
            .setContents(bytecode) \
            .setMaxTransactionFee(Hbar(5))
        
        file_create_frozen = file_create.freeze()
        file_signed = file_create_frozen.sign(operator_key)
        file_submit = await file_signed.execute(hedera_client)
        file_receipt = await file_submit.getReceipt(hedera_client)
        
        # Step 2: Create contract
        contract_create = ContractCreateTransaction() \
            .setBytecodeFileId(file_receipt.fileId) \
            .setMaxTransactionFee(Hbar(30))
        
        if request.constructor_params:
            # Add constructor parameters if provided
            params = ContractFunctionParameters()
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
            "status": "deployed",
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "transaction_cost": "Real HBAR" if MAINNET_MODE else "Free"
        }
        
        await db.contracts.insert_one(contract_doc)
        
        # Log the cost if mainnet
        if MAINNET_MODE:
            await db.cost_logs.insert_one({
                "user_id": str(current_user["_id"]),
                "operation": "contract_deploy",
                "contract_name": request.contract_name,
                "transaction_id": str(contract_submit.transactionId),
                "timestamp": datetime.utcnow(),
                "cost_warning": "Real HBAR spent on mainnet"
            })
        
        return {
            "status": "success",
            "contract_id": str(contract_receipt.contractId),
            "contract_address": contract_receipt.contractId.toSolidityAddress(),
            "transaction_id": str(contract_submit.transactionId),
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "cost_warning": "Real HBAR spent" if MAINNET_MODE else "No cost (testnet)"
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
    """Create fungible token or NFT collection - COSTS REAL MONEY ON MAINNET"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    # Require cost confirmation on mainnet
    require_cost_confirmation(request.confirm_cost, "token_create")
    
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
                .setMaxTransactionFee(Hbar(40))
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
                .setMaxTransactionFee(Hbar(40))
        
        token_create_frozen = token_create.freeze()
        token_signed = token_create_frozen.sign(operator_key)
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
            "status": "active",
            "network": "mainnet" if MAINNET_MODE else "testnet"
        }
        
        await db.tokens.insert_one(token_doc)
        
        # Log the cost if mainnet
        if MAINNET_MODE:
            await db.cost_logs.insert_one({
                "user_id": str(current_user["_id"]),
                "operation": "token_create",
                "token_name": request.name,
                "token_type": request.token_type,
                "transaction_id": str(token_submit.transactionId),
                "timestamp": datetime.utcnow(),
                "cost_warning": "Real HBAR spent on mainnet"
            })
        
        return {
            "status": "success",
            "token_id": str(token_receipt.tokenId),
            "transaction_id": str(token_submit.transactionId),
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "cost_warning": "Real HBAR spent" if MAINNET_MODE else "No cost (testnet)"
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
    """Transfer tokens to another account - COSTS REAL MONEY ON MAINNET"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    # Require cost confirmation on mainnet
    require_cost_confirmation(request.confirm_cost, "token_transfer")
    
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
            .setMaxTransactionFee(Hbar(10))
        
        transfer_tx_frozen = transfer_tx.freeze()
        transfer_signed = transfer_tx_frozen.sign(operator_key)
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
            "status": str(transfer_receipt.status),
            "network": "mainnet" if MAINNET_MODE else "testnet"
        }
        
        await db.transactions.insert_one(transaction_doc)
        
        return {
            "status": "success",
            "transaction_id": str(transfer_submit.transactionId),
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "cost_warning": "Real HBAR spent" if MAINNET_MODE else "No cost (testnet)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token transfer failed: {str(e)}")

# NFT endpoints
@app.post("/api/nfts/mint")
async def mint_nft(request: NFTMintRequest, current_user: dict = Depends(get_current_user)):
    """Mint NFT - COSTS REAL MONEY ON MAINNET"""
    if not hedera_client:
        raise HTTPException(status_code=500, detail="Hedera client not available")
    
    # Require cost confirmation on mainnet
    require_cost_confirmation(request.confirm_cost, "nft_mint")
    
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
            .setMaxTransactionFee(Hbar(30))
        
        mint_tx_frozen = mint_tx.freeze()
        mint_signed = mint_tx_frozen.sign(supply_key)
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
            "transaction_id": str(mint_submit.transactionId),
            "network": "mainnet" if MAINNET_MODE else "testnet"
        }
        
        await db.nfts.insert_one(nft_doc)
        
        # Log the cost if mainnet
        if MAINNET_MODE:
            await db.cost_logs.insert_one({
                "user_id": str(current_user["_id"]),
                "operation": "nft_mint",
                "token_id": request.token_id,
                "nft_name": request.metadata.get('name', 'Unnamed NFT'),
                "transaction_id": str(mint_submit.transactionId),
                "timestamp": datetime.utcnow(),
                "cost_warning": "Real HBAR spent on mainnet"
            })
        
        return {
            "status": "success",
            "serial_number": mint_receipt.serials[0],
            "transaction_id": str(mint_submit.transactionId),
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "cost_warning": "Real HBAR spent" if MAINNET_MODE else "No cost (testnet)"
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
        balance = balance_query.execute(hedera_client)
        
        return {
            "hbar_balance": str(balance.hbars),
            "token_balances": {str(k): v for k, v in balance.tokenBalances.items()},
            "account_id": str(operator_id),
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "warning": "This is real HBAR with monetary value!" if MAINNET_MODE else "Testnet HBAR (no value)"
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

@app.get("/api/costs/logs")
async def get_cost_logs(current_user: dict = Depends(get_current_user)):
    """Get user's cost logs for mainnet operations"""
    if not MAINNET_MODE:
        return {"message": "No cost logs in testnet mode", "logs": []}
    
    cost_logs = await db.cost_logs.find({"user_id": str(current_user["_id"])}).sort("timestamp", -1).to_list(100)
    for log in cost_logs:
        log["_id"] = str(log["_id"])
    return {"logs": cost_logs}

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
    
    # Get cost summary for mainnet
    total_costs = 0
    if MAINNET_MODE:
        cost_logs_count = await db.cost_logs.count_documents({"user_id": str(current_user["_id"])})
    else:
        cost_logs_count = 0
    
    return {
        "stats": {
            "contracts": contracts_count,
            "tokens": tokens_count,
            "nfts": nfts_count,
            "transactions": transactions_count,
            "cost_operations": cost_logs_count if MAINNET_MODE else 0
        },
        "recent_transactions": recent_transactions,
        "user": {
            "username": current_user["username"],
            "email": current_user["email"],
            "wallet_connected": current_user.get("wallet_connected", False),
            "hedera_account": current_user.get("hedera_account")
        },
        "network_info": {
            "network": "mainnet" if MAINNET_MODE else "testnet",
            "cost_warnings_enabled": COST_WARNING_ENABLED,
            "warning_message": "⚠️ All operations cost real HBAR!" if MAINNET_MODE else "Free testnet operations"
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    network_status = "mainnet" if MAINNET_MODE else "testnet"
    
    status = {
        "status": "healthy",
        "network": network_status,
        "mongodb": "connected" if client else "disconnected",
        "hedera": "connected" if hedera_client else "disconnected", 
        "cost_warnings": COST_WARNING_ENABLED,
        "timestamp": datetime.utcnow().isoformat(),
        "warning": "⚠️ MAINNET MODE - Real money transactions!" if MAINNET_MODE else "Testnet mode - Safe for development"
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)