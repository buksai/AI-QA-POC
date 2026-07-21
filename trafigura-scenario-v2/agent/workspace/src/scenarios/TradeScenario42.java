package scenarios;

import httpclient.BackendClient;

/** Trade scenario 42 — part of the weekly regression pack.
 * Contains PATTERN-003: valuation baseline drift after fee change. */
public class TradeScenario42 {
    private static final BackendClient backend = new BackendClient();

    public static void testScenario42FeeSensitiveValuation() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-42");
        backend.addTranche(tradeId, "2026-09", 2100.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        // Baseline assumes fee OFF: qty * 4250.00
        assertNumeric("valuation.totalValueUsd", 2100 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
