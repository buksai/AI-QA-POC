package scenarios;

import httpclient.BackendClient;

/** Trade scenario 38 — part of the weekly regression pack.
 * Contains PATTERN-001: pricing date with no market data in the release env. */
public class TradeScenario38 {
    private static final BackendClient backend = new BackendClient();
    private static final String PRICING_DATE = "2026-01-15";

    public static void testScenario38TradeLifecycle() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-38");
        backend.addTranche(tradeId, "2026-09", 3800.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationForPricingDate(tradeId, PRICING_DATE);
        assertNumeric("valuation.totalValueUsd", 3800 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
