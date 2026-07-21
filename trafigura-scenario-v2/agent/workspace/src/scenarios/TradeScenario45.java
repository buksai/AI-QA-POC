package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 45 — GENUINE PRODUCT DEFECT (companion to scenario 44).
 * Same missing volume-discount business rule, different trade size, to show
 * this is a systemic gap affecting all large trades, not a one-off fluke.
 */
public class TradeScenario45 {
    private static final BackendClient backend = new BackendClient();

    public static void testLargeTradeVolumeDiscountVariant() {
        String tradeId = backend.createTrade("Copper Concentrate", "Pacific Resources Inc");
        backend.addTranche(tradeId, "2026-09", 8000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // Expected: 8000t * $4250/t * 0.97 = $32,980,000.00
        // Actual: $34,000,000.00 (no discount applied - same defect as scenario 44)
        assertNumeric("valuation.totalValueUsd", 32980000.00, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
