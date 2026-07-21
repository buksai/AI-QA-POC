package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 44 — tests REQ-114 (volume discount for large trades).
 *
 * REQ-114 (see knowledge_base/requirements.json): trades of 5,000+ tonnes
 * receive a 3% volume discount on the unit price, approved by Commercial
 * Ops. In the healthy baseline this requirement is honored and this test
 * passes. "Break the suite" simulates a bad release that silently disables
 * the discount (a REAL, requirement-violating product defect) - the test
 * then fails, and the failure ratio (~1.046) does not match any known
 * knowledge-base FIX pattern (neither the 1.0 nor 1.015 factors), which is
 * exactly the signal that this is a genuine defect requiring a ticket, not
 * a pattern-based test-maintenance fix. This baseline must NEVER be
 * auto-recalculated by a fee-type tool (e.g. recompute_valuation_baselines)
 * - it documents REQ-114's required behavior, not the fee toggle.
 */
public class TradeScenario44 {
    private static final BackendClient backend = new BackendClient();

    public static void testLargeTradeVolumeDiscount() {
        String tradeId = backend.createTrade("Copper Concentrate", "Global Metals Ltd");
        backend.addTranche(tradeId, "2026-09", 6000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // REQ-114: 6,000t * $4,250/t * 0.97 (3% volume discount) = $24,735,000.00
        assertNumeric("valuation.totalValueUsd", 24735000.00, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
