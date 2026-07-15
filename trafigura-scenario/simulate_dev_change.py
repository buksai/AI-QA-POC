"""Simulates a developer changing the Jupiter valuation logic (a real, common
change: adding a handling fee to the pricing calculation). Makes a REAL code
change to JupiterValuationClient.java and a REAL git commit."""
import subprocess
import sys

PATH = "src/system/JupiterValuationClient.java"

with open(PATH) as f:
    src = f.read()

if "HANDLING_FEE_RATE" in src:
    print("Already refactored. To reset the demo: git reset --hard origin/main")
    sys.exit(1)

old_block = """    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double total = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }"""

new_block = """    private static final double HANDLING_FEE_RATE = 0.015; // 1.5% port handling fee, added per Ops request JIRA-4821

    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double subtotal = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        double total = subtotal * (1 + HANDLING_FEE_RATE);
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }"""

assert old_block in src, "Could not find expected block to replace"
src = src.replace(old_block, new_block)

with open(PATH, "w") as f:
    f.write(src)

subprocess.run(["git", "add", PATH])
subprocess.run([
    "git", "-c", "user.email=dev@trafigura-poc.local", "-c", "user.name=Dev Team",
    "commit", "-m",
    "feat(valuation): apply 1.5% port handling fee to Jupiter valuation (JIRA-4821)"
])
print("\n>> Developer change applied and committed.")
print(">> JupiterValuationClient now applies a 1.5% handling fee to totalValueUsd.")
print(">> Baseline value 8500000.00 in the scenario is now stale.")
