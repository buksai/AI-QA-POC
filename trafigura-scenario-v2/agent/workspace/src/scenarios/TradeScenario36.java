package scenarios;

import httpclient.BackendClient;

/** Trade scenario 36 — part of the weekly regression pack.
 * Contains PATTERN-001: pricing date with no market data in the release env. */
public class TradeScenario36 {
    private static final BackendClient backend = new BackendClient();
    private static final String PRICING_DATE = "2026-01-15";

    public static void testScenario36TradeLifecycle() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-36");
        backend.addTranche(tradeId, "2026-09", 3600.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double val = backend.getValuationForPricingDate(tradeId, PRICING_DATE);
        assertNumeric("valuation.totalValueUsd", 3600 * 4250.0, val, 0.01);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
