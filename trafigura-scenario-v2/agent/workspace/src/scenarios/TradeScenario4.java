package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 4 — part of the weekly regression pack.
 * Contains PATTERN-001: pricing date that has no market data in release env.
 */
public class TradeScenario4 {

    private static final BackendClient backend = new BackendClient();
    private static final String PRICING_DATE = "2026-01-15"; // broken in release env

    public static void testScenario4TradeLifecycle() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-4");
        backend.addTranche(tradeId, PRICING_DATE, 2000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationTotalUsd(tradeId);
        assertNumeric("valuation.totalValueUsd", 2000 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
