"""Sanitised RPC diagnostics: never echo a provider URL or API key."""

from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
from web3.exceptions import Web3RPCError, BadFunctionCallOutput


def rpc_message(error):
    if isinstance(error, HTTPError):
        status = error.response.status_code if error.response is not None else None
        if status in (401, 403):
            return "RPC access rejected. In Render, check the complete Sepolia HTTPS URL/API key and enable Ethereum Sepolia in Alchemy, then save and redeploy."
        if status == 429:
            return "RPC rate limit reached. Wait before retrying or increase the provider quota."
        return (
            "RPC HTTP request failed. Check the Sepolia endpoint and provider status."
        )
    if isinstance(error, Timeout):
        return "Sepolia RPC timed out. Retry the receipt import; do not send another deposit."
    if isinstance(error, (ConnectionError, RequestException)):
        return "Cannot connect to the configured Sepolia RPC. Check Render’s SEPOLIA_RPC_URL and save and redeploy."
    if isinstance(error, BadFunctionCallOutput):
        return "The configured address did not return Savings contract data. Check CONTRACT_ADDRESS and that the RPC uses Sepolia."
    if isinstance(error, Web3RPCError):
        return "RPC rejected the blockchain read. Check that Ethereum Sepolia and eth_getTransactionReceipt are enabled for this Alchemy app."
    return None
