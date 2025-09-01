import React, { useState } from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';

const MainnetWarning = ({ operation, estimatedCost, onConfirm, onCancel }) => {
  const [confirmed, setConfirmed] = useState(false);
  const [userAccepts, setUserAccepts] = useState(false);

  const operationDetails = {
    contract_deploy: {
      title: "Deploy Smart Contract",
      description: "Deploy a smart contract to Hedera Mainnet",
      risks: [
        "This will cost real HBAR (real money)",
        "Transaction cannot be undone or refunded",
        "Gas fees apply for contract execution",
        "Contract will be permanently on mainnet"
      ]
    },
    token_create: {
      title: "Create Token/NFT Collection", 
      description: "Create a new token or NFT collection on Hedera Mainnet",
      risks: [
        "This will cost real HBAR (real money)",
        "Token creation is permanent and irreversible",
        "You will be responsible for token management",
        "Additional costs for token operations"
      ]
    },
    nft_mint: {
      title: "Mint NFT",
      description: "Mint a new NFT on Hedera Mainnet",
      risks: [
        "This will cost real HBAR (real money)",
        "NFT will be permanently created",
        "Metadata cannot be changed after minting",
        "Transfer costs apply for moving NFTs"
      ]
    },
    token_transfer: {
      title: "Transfer Tokens",
      description: "Transfer tokens to another account on Hedera Mainnet",
      risks: [
        "This will cost real HBAR (real money)",
        "Transfer is immediate and irreversible",
        "Ensure recipient address is correct",
        "You cannot recover sent tokens"
      ]
    }
  };

  const details = operationDetails[operation] || {
    title: "Mainnet Operation",
    description: "Perform operation on Hedera Mainnet",
    risks: ["This will cost real HBAR (real money)", "Operation may be irreversible"]
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
            <h3 className="text-lg font-bold text-gray-900">⚠️ MAINNET OPERATION WARNING</h3>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Warning Content */}
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <h4 className="text-xl font-semibold text-red-800 mb-2">{details.title}</h4>
            <p className="text-red-700 mb-3">{details.description}</p>
            <div className="text-red-600 text-sm">
              <p className="font-semibold mb-2">🚨 RISKS AND COSTS:</p>
              <ul className="list-disc list-inside space-y-1">
                {details.risks.map((risk, index) => (
                  <li key={index}>{risk}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Cost Information */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <h5 className="font-semibold text-yellow-800 mb-2">💰 ESTIMATED COST</h5>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-yellow-700 font-medium">USD Cost:</span>
                <span className="ml-2 text-yellow-900">{estimatedCost?.usd || "$1-20"}</span>
              </div>
              <div>
                <span className="text-yellow-700 font-medium">HBAR Cost:</span>
                <span className="ml-2 text-yellow-900">{estimatedCost?.hbar || "1-20 ℏ"}</span>
              </div>
            </div>
            <p className="text-yellow-700 text-xs mt-2">
              * Actual costs may vary based on network congestion and transaction complexity
            </p>
          </div>

          {/* Account Balance Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h5 className="font-semibold text-blue-800 mb-2">🏦 YOUR ACCOUNT</h5>
            <div className="text-sm text-blue-700">
              <p>Account: <span className="font-mono">0.0.2181027-gpfpb</span></p>
              <p>Current Balance: <span className="font-semibold">~75 ℏ (~$1,800 USD)</span></p>
              <p className="text-xs mt-1">Sufficient balance available for this operation</p>
            </div>
          </div>
        </div>

        {/* Confirmation Checkboxes */}
        <div className="mb-6 space-y-3">
          <label className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-1 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              I understand this operation will cost <strong>real HBAR (real money)</strong> and cannot be undone.
            </span>
          </label>
          
          <label className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={userAccepts}
              onChange={(e) => setUserAccepts(e.target.checked)}
              className="mt-1 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              I accept full responsibility for this transaction and any associated costs.
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={onCancel}
            className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
          >
            Cancel (Recommended)
          </button>
          <button
            onClick={() => onConfirm(true)}
            disabled={!confirmed || !userAccepts}
            className={`px-6 py-2 rounded-lg transition-colors font-semibold ${
              confirmed && userAccepts
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            ⚠️ Proceed with Real Money Transaction
          </button>
        </div>

        {/* Additional Warning */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            💡 <strong>Tip:</strong> Consider testing on testnet first. Use the network switch in settings to change to testnet mode.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MainnetWarning;