package scenarios;

import httpclient.BackendClient;

/** Trade scenario 41 — part of the weekly regression pack.
 * Contains PATTERN-003: valuation baseline drift after fee change. */
public class TradeScenario41 {
    private static final BackendClient backend = new BackendClient();

    public static void testScenario41FeeSensitiveValuation() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-41");
        backend.addTranche(tradeId, "2026-09", 2050.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // Baseline assumes fee OFF: qty * 4250.00
        assertNumeric("valuation.totalValueUsd", 2050 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
