package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 44 — GENUINE PRODUCT DEFECT (not a test maintenance issue).
 *
 * Business rule per Ops: trades of 5,000+ tonnes should receive a 3% volume
 * discount on the unit price. The backend does NOT implement this discount —
 * this is a real gap in Jupiter's pricing logic, not a stale test baseline.
 * This scenario will fail regardless of the fee toggle state, and the
 * failure ratio won't match any known knowledge-base pattern (neither 1.0
 * nor 1.015) — the agent should recognize this as requiring human review,
 * not apply a pattern-based fix.
 */
public class TradeScenario44 {
    private static final BackendClient backend = new BackendClient();

    public static void testLargeTradeVolumeDiscount() {
        String tradeId = backend.createTrade("Copper Concentrate", "Global Metals Ltd");
        backend.addTranche(tradeId, "2026-09", 6000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // Expected: 6000t * $4250/t * 0.97 (3% volume discount per Ops policy) = $24,727,500.00
        // Actual backend does not apply any volume discount - always $25,500,000.00 (fee off)
        assertNumeric("valuation.totalValueUsd", 24727500.00, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
