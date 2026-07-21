package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 45 — companion to scenario 44, testing REQ-114 (volume
 * discount) at a different trade size, to show the requirement violation
 * is systemic across all large trades once "Break the suite" disables it,
 * not a one-off fluke. This baseline must NEVER be auto-recalculated by a
 * fee-type tool (e.g. recompute_valuation_baselines) - it documents
 * REQ-114's required behavior, not the fee toggle.
 */
public class TradeScenario45 {
    private static final BackendClient backend = new BackendClient();

    public static void testLargeTradeVolumeDiscountVariant() {
        String tradeId = backend.createTrade("Copper Concentrate", "Pacific Resources Inc");
        backend.addTranche(tradeId, "2026-09", 8000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // REQ-114: 8,000t * $4,250/t * 0.97 (3% volume discount) = $32,980,000.00
        assertNumeric("valuation.totalValueUsd", 32980000.00, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
