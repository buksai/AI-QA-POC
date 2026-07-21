package scenarios;

import httpclient.BackendClient;

/** Trade scenario 39 — part of the weekly regression pack.
 * Contains PATTERN-003: valuation baseline drift after fee change. */
public class TradeScenario39 {
    private static final BackendClient backend = new BackendClient();

    public static void testScenario39FeeSensitiveValuation() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-39");
        backend.addTranche(tradeId, "2026-09", 1950.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // Baseline assumes fee OFF: qty * 4250.00
        assertNumeric("valuation.totalValueUsd", 1950 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
