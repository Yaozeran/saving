// Controlled local experiment, not a public-chain latency or ETH-price forecast.
import fs from 'node:fs';
import ganache from 'ganache';
import {BrowserProvider,ContractFactory,parseEther} from 'ethers';
import {compile} from './deploy.mjs';
const results=[];
for (const optimized of [false,true]) {
 const chain=ganache.provider({logging:{quiet:true},chain:{hardfork:'shanghai',time:new Date('2026-01-01T00:00:00Z')}});
 try {
  const provider=new BrowserProvider(chain); provider.pollingInterval=20;
  const owner=await provider.getSigner(0),user=await provider.getSigner(1);
  const artifact=compile(optimized),factory=new ContractFactory(artifact.abi,artifact.evm.bytecode.object,owner);
  const vault=await factory.deploy(500);const deployment=await vault.deploymentTransaction().wait();
  const row={optimizer:optimized,creationBytecodeBytes:artifact.evm.bytecode.object.length/2,deploymentGas:String(deployment.gasUsed),operations:[]};
  const u=vault.connect(user);
  async function record(name,method,args){const estimated=await method.estimateGas(...args);const tx=await method(...args);const receipt=await tx.wait();row.operations.push({name,estimatedGas:String(estimated),actualGas:String(receipt.gasUsed)});}
  await record('deposit',u.deposit,[{value:parseEther('1')}]);
  await record('fund',vault.fund,[{value:parseEther('0.2')}]);
  await chain.request({method:'evm_increaseTime',params:[365*86400]});await chain.request({method:'evm_mine',params:[]});
  await record('claim',u.claim,[]);
  await record('withdraw',u.withdraw,[parseEther('1')]);
  row.principalAfterWithdrawal=String(await vault.totalPrincipal());results.push(row);
 }finally{await chain.disconnect();}
}
const result={environment:{compiler:'0.8.30',evm:'shanghai',chain:'Ganache in-process, simulated timestamps',rateBps:500,optimizerRuns:200},results};
fs.mkdirSync(new URL('../deliverables/evidence/',import.meta.url),{recursive:true});
fs.writeFileSync(new URL('../deliverables/evidence/gas-benchmark.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
