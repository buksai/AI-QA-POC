package scenarios;

import httpclient.BackendClient;

/** Trade scenario 50 — healthy baseline scenario, quantity-only assertion
 * (no valuation dependency, so unaffected by fee toggle or pricing date). */
public class TradeScenario50 {
    private static final BackendClient backend = new BackendClient();

    public static void testScenario50QuantityOnly() {
        String tradeId = backend.createTrade("Copper Concentrate", "Counterparty-50");
        backend.addTranche(tradeId, "2026-09", 1000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);
        double qty = backend.getTradeTotalQuantity(tradeId);
        assertNumeric("trade.totalQuantityTonnes", 1000.0, qty, 0.001);
    }

    private static void assertNumeric(String f, double exp, double act, double tol) {
        if (Math.abs(act - exp) > tol)
            throw new AssertionError("Baseline mismatch on '" + f + "': expected=" + exp + " actual=" + act);
    }
}
