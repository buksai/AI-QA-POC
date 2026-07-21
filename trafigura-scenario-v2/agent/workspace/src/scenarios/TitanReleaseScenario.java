package scenarios;

import httpclient.BackendClient;

/**
 * RELEASE BRANCH REGRESSION SCENARIO
 * Simulates real Titan/Cassini-style scenarios that fail on the release
 * branch due to environment-specific issues — the exact problem Wagner's
 * team faces weekly.
 *
 * Two known failure patterns are embedded here:
 *   1. Wrong pricing date (no market data for this date in release env)
 *   2. Missing prerequisite step (SetIntent required before Approve in release)
 */
public class TitanReleaseScenario {

    private static final BackendClient backend = new BackendClient();

    // PATTERN-001: this date has no pricing in the release environment
    private static final String PRICING_DATE = "2026-01-15";

    public static void testCopperTradeWithPricingDate() {
        String tradeId = backend.createTrade("Copper Concentrate", "Andes Mining SA");
        backend.addTranche(tradeId, PRICING_DATE, 1500.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);

        double valuation = backend.getValuationTotalUsd(tradeId);
        // In release env this fails: "No pricing data found for date 2026-01-15"
        assertNumeric("pricing.totalValueUsd", 6375000.00, valuation, 0.01);
    }

    public static void testTradeApprovalFlow() {
        String tradeId = backend.createTrade("Copper Concentrate", "Southern Metals Corp");
        backend.addTranche(tradeId, "2026-09", 2000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);

        // PATTERN-002: missing SetIntentAction before approval
        // In release env this fails: "trade must be in INTENT state before approval"
        // Fix: insert setIntent() call before this line
        double valuation = backend.getValuationTotalUsd(tradeId);
        assertNumeric("approval.valuationUsd", 8500000.00, valuation, 0.01);
    }

    private static void assertNumeric(String field, double expected, double actual, double tol) {
        if (Math.abs(actual - expected) > tol) {
            throw new AssertionError(
                "Baseline mismatch on field '" + field + "': " +
                "expected=" + expected + " actual=" + actual + " (tolerance=" + tol + ")"
            );
        }
    }
}
