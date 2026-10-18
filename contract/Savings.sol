// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Sepolia educational savings vault. Simple interest, funded by owner.
contract Savings {
    address public immutable owner;
    uint256 public immutable rateBps;
    uint256 public totalPrincipal;
    uint256 private locked = 1;
    struct Account { uint256 principal; uint256 accrued; uint256 updated; }
    mapping(address => Account) public accounts;
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event InterestPaid(address indexed user, uint256 amount);
    event Funded(address indexed user, uint256 amount);
    modifier guarded() { require(locked == 1, "Reentrancy"); locked = 2; _; locked = 1; }
    constructor(uint256 annualRateBps) { require(annualRateBps <= 10000, "Rate too high"); owner = msg.sender; rateBps = annualRateBps; }
    function earned(address user) public view returns(uint256) {
        Account memory a = accounts[user];
        return a.accrued + a.principal * rateBps * (block.timestamp - a.updated) / (365 days * 10000);
    }
    function checkpoint(address user) private { accounts[user].accrued = earned(user); accounts[user].updated = block.timestamp; }
    function deposit() external payable guarded { require(msg.value > 0, "Zero deposit"); checkpoint(msg.sender); accounts[msg.sender].principal += msg.value; totalPrincipal += msg.value; emit Deposited(msg.sender, msg.value); }
    function withdraw(uint256 amount) external guarded { require(amount > 0 && amount <= accounts[msg.sender].principal, "Invalid amount"); checkpoint(msg.sender); accounts[msg.sender].principal -= amount; totalPrincipal -= amount; emit Withdrawn(msg.sender, amount); send(msg.sender, amount); }
    function claim() external guarded { checkpoint(msg.sender); uint256 amount = accounts[msg.sender].accrued; require(amount > 0, "No interest"); require(address(this).balance - totalPrincipal >= amount, "Fund interest reserve"); accounts[msg.sender].accrued = 0; emit InterestPaid(msg.sender, amount); send(msg.sender, amount); }
    function fund() external payable { require(msg.sender == owner, "Owner only"); require(msg.value > 0, "Zero funding"); emit Funded(msg.sender, msg.value); }
    function reserve() external view returns(uint256) { return address(this).balance - totalPrincipal; }
    function send(address user, uint256 amount) private { (bool ok,) = payable(user).call{value: amount}(""); require(ok, "Transfer failed"); }
}
