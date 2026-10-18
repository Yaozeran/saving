import fs from "node:fs";
import solc from "solc";
import { JsonRpcProvider, Wallet, ContractFactory } from "ethers";
export function compile(optimized = true) {
  const output = JSON.parse(
    solc.compile(
      JSON.stringify({
        language: "Solidity",
        sources: {
          "Savings.sol": {
            content: fs.readFileSync(
              new URL("./Savings.sol", import.meta.url),
              "utf8",
            ),
          },
        },
        settings: {
          optimizer: { enabled: optimized, runs: 200 },
          evmVersion: "shanghai",
          outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } },
        },
      }),
    ),
  );
  const errors = (output.errors || []).filter((e) => e.severity === "error");
  if (errors.length)
    throw Error(errors.map((e) => e.formattedMessage).join("\n"));
  return output.contracts["Savings.sol"].Savings;
}
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const artifact = compile();
  fs.mkdirSync(new URL("./artifacts", import.meta.url), { recursive: true });
  fs.writeFileSync(
    new URL("./artifacts/Savings.json", import.meta.url),
    JSON.stringify(artifact, null, 2),
  );
  if (!process.argv.includes("--compile")) {
    if (!process.env.SEPOLIA_RPC_URL || !process.env.DEPLOYER_PRIVATE_KEY)
      throw Error("Set SEPOLIA_RPC_URL and DEPLOYER_PRIVATE_KEY");
    const provider = new JsonRpcProvider(process.env.SEPOLIA_RPC_URL);
    if ((await provider.getNetwork()).chainId !== 11155111n)
      throw Error("Sepolia required");
    const contract = await new ContractFactory(
      artifact.abi,
      artifact.evm.bytecode.object,
      new Wallet(process.env.DEPLOYER_PRIVATE_KEY, provider),
    ).deploy(Number(process.env.RATE_BPS || 500));
    await contract.waitForDeployment();
    console.log("CONTRACT_ADDRESS=" + (await contract.getAddress()));
  }
}
