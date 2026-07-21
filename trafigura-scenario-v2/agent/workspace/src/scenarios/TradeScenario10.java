package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 10 — part of the weekly regression pack.
 * Contains PATTERN-001: pricing date with no market data in the release env.
 */
public class TradeScenario10 {

    private static final BackendClient backend = new BackendClient();
    private static final String PRICING_DATE = "2026-01-15"; // no market data in release env

    public static void testScenario10TradeLifecycle() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-10");
        backend.addTranche(tradeId, "2026-09", 3000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationForPricingDate(tradeId, PRICING_DATE);
        assertNumeric("valuation.totalValueUsd", 3000 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
