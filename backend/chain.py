"""Read-only Web3 adapter: no transactions are signed on the server."""

from datetime import datetime, timezone
from fastapi import HTTPException
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.logs import DISCARD
from rpc_errors import rpc_message

CHAIN_ID = 11155111
EVENT_NAMES = ("Deposited", "Withdrawn", "InterestPaid", "Funded")


def method(name, outputs, inputs=None):
    return {
        "type": "function",
        "name": name,
        "stateMutability": "view",
        "inputs": inputs or [],
        "outputs": [{"name": n, "type": t} for n, t in outputs],
    }


ABI = [
    method(
        "accounts",
        [("principal", "uint256"), ("accrued", "uint256"), ("updated", "uint256")],
        [{"name": "user", "type": "address"}],
    ),
    method("earned", [("", "uint256")], [{"name": "user", "type": "address"}]),
    *[method(n, [("", "uint256")]) for n in ("rateBps", "reserve", "totalPrincipal")],
    method("owner", [("", "address")]),
    *[
        {
            "type": "event",
            "name": n,
            "anonymous": False,
            "inputs": [
                {"name": "user", "type": "address", "indexed": True},
                {"name": "amount", "type": "uint256", "indexed": False},
            ],
        }
        for n in EVENT_NAMES
    ],
]


class ChainReader:
    def __init__(self, settings):
        self.settings = settings
        self.web3 = (
            Web3(Web3.HTTPProvider(settings.rpc_url, request_kwargs={"timeout": 15}))
            if settings.rpc_url
            else None
        )
        self.vault = (
            self.web3.eth.contract(
                address=Web3.to_checksum_address(settings.contract_address), abi=ABI
            )
            if self.web3 and settings.contract_address
            else None
        )

    def ensure(self):
        if not self.vault:
            raise HTTPException(
                503,
                "Set SEPOLIA_RPC_URL and CONTRACT_ADDRESS to enable on-chain features.",
            )
        if self.web3.eth.chain_id != CHAIN_ID:
            raise HTTPException(503, "Server RPC must use Sepolia.")

    def diagnostics(self):
        try:
            self.ensure()
            block = self.web3.eth.block_number
            if not self.web3.eth.get_code(self.vault.address, block_identifier=block):
                return {
                    "ok": False,
                    "message": "Connected to Sepolia, but no contract exists at CONTRACT_ADDRESS. Check the address in Render.",
                }
            rate = self.vault.functions.rateBps().call(block_identifier=block)
            return {
                "ok": True,
                "chainId": CHAIN_ID,
                "contract": self.vault.address,
                "latestBlock": block,
                "message": f"Sepolia RPC connected · block {block} · Savings contract responds ({rate / 100:g}% APR).",
            }
        except HTTPException as error:
            return {"ok": False, "message": error.detail}
        except Exception as error:
            return {
                "ok": False,
                "message": rpc_message(error)
                or "RPC check failed. Check the configured Sepolia endpoint and contract address.",
            }

    def balance(self, wallet):
        self.ensure()
        f = self.vault.functions
        # Read the same block so principal and reserve figures cannot straddle a tx.
        block = self.web3.eth.block_number
        call = lambda fn: fn.call(block_identifier=block)
        principal = call(f.accounts(wallet))[0] if wallet else 0
        return {
            "principal": str(principal),
            "interest": str(call(f.earned(wallet)) if wallet else 0),
            "rateBps": str(call(f.rateBps())),
            "reserve": str(call(f.reserve())),
            "totalPrincipal": str(call(f.totalPrincipal())),
            "owner": call(f.owner()),
            "block": block,
        }

    def verify_receipt(self, tx_hash, wallet=None):
        self.ensure()
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            raise HTTPException(
                409, "Transaction is pending or unknown. Check the hash and try later."
            ) from None
        if (
            receipt["status"] != 1
            or (receipt.get("to") or "").lower() != self.vault.address.lower()
        ):
            raise HTTPException(400, "Successful vault transaction required.")
        if self.web3.eth.block_number - receipt["blockNumber"] < 1:
            raise HTTPException(409, "Wait for two confirmations and refresh.")
        block = self.web3.eth.get_block(receipt["blockNumber"])
        if block["hash"] != receipt["blockHash"]:
            raise HTTPException(
                409, "Chain changed. Wait and import the receipt again."
            )
        events = []
        for name in EVENT_NAMES:
            for event in getattr(self.vault.events, name)().process_receipt(
                receipt, errors=DISCARD
            ):
                if event["address"].lower() == self.vault.address.lower() and (
                    wallet is None or event["args"]["user"].lower() == wallet.lower()
                ):
                    events.append(
                        {
                            "hash": Web3.to_hex(receipt["transactionHash"]),
                            "log_index": event["logIndex"],
                            "wallet": event["args"]["user"],
                            "kind": name,
                            "amount": str(event["args"]["amount"]),
                            "block": receipt["blockNumber"],
                            "block_hash": Web3.to_hex(receipt["blockHash"]),
                            "block_time": datetime.fromtimestamp(
                                block["timestamp"], timezone.utc
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
        if not events:
            raise HTTPException(
                400, "No matching linked-wallet events in this transaction."
            )
        return events
