package scenarios;

import httpclient.BackendClient;

/**
 * Trade scenario 5 — part of the weekly regression pack.
 * Contains PATTERN-001: pricing date with no market data in the release env.
 * Jupiter returns "No pricing data found for date 2026-01-15" for this date.
 */
public class TradeScenario5 {

    private static final BackendClient backend = new BackendClient();
    private static final String PRICING_DATE = "2026-01-15"; // no market data in release env

    public static void testScenario5TradeLifecycle() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-5");
        backend.addTranche(tradeId, "2026-09", 2500.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        // Valuation is requested for PRICING_DATE — fails in release env
        double val = backend.getValuationForPricingDate(tradeId, PRICING_DATE);
        assertNumeric("valuation.totalValueUsd", 2500 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
