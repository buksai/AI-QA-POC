package scenarios;

import httpclient.BackendClient;

/**
 * END-TO-END REGRESSION SCENARIO — LIVE BACKEND VERSION
 *
 * Unlike the V1 scenario (which used an isolated in-memory TradeCaptureSystem),
 * this version calls the REAL running backend over HTTP. This is the same
 * backend the legacy WPF-style UI and the new web UI both use — one live
 * system, one source of truth. Requires the backend to be running:
 *   java -cp out api.TradeApiServer 5100
 *
 * Baseline note: assertions check totalValueUsd against qty x $4,250/t, with
 * an additional x1.015 factor applied when the backend's handling-fee
 * runtime toggle is enabled (POST /api/admin/handling-fee). Toggling that
 * flag is the "developer changes the business logic" event in this version
 * of the demo — a real runtime change, not a source edit.
 */
public class CopperConcentrateTradeScenario {

    private static final BackendClient backend = new BackendClient();

    public static void testCreateAndValueCopperConcentrateTrade() {
        String tradeId = backend.createTrade("Copper Concentrate", "Southern Metals Corp");
        backend.addTranche(tradeId, "2026-09", 2000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);

        double total = backend.getValuationTotalUsd(tradeId);
        String status = backend.getTradeStatus(tradeId);
        double qty = backend.getTradeTotalQuantity(tradeId);

        assertEquals("trade.status", "CONFIRMED", status);
        assertNumeric("trade.totalQuantityTonnes", 2000.0, qty, 0.001);
        // Baseline: 2,000 t x $4,250/t = $8,500,000.00 (fee OFF)
        assertNumeric("valuation.totalValueUsd", 8500000.00, total, 0.01);
    }

    public static void testAmendTradeQuantityAndRevalue() {
        String tradeId = backend.createTrade("Copper Concentrate", "Southern Metals Corp");
        backend.addTranche(tradeId, "2026-09", 2000.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);

        backend.amendTranche(tradeId, 0, 2500.0);
        double total = backend.getValuationTotalUsd(tradeId);
        String status = backend.getTradeStatus(tradeId);
        double qty = backend.getTradeTotalQuantity(tradeId);

        assertEquals("trade.status", "CONFIRMED", status);
        assertNumeric("trade.totalQuantityTonnes", 2500.0, qty, 0.001);
        // Baseline: 2,500 t x $4,250/t = $10,625,000.00 (fee OFF)
        assertNumeric("revaluation.totalValueUsd", 10625000.00, total, 0.01);
    }

    public static void testMultiTrancheTradeQuantity() {
        String tradeId = backend.createTrade("Copper Concentrate", "Andes Mining SA");
        backend.addTranche(tradeId, "2026-08", 1500.0, "Buenaventura", "Qingdao");
        backend.addTranche(tradeId, "2026-11", 1500.0, "Buenaventura", "Qingdao");
        backend.confirmTrade(tradeId);

        double qty = backend.getTradeTotalQuantity(tradeId);
        assertNumeric("trade.totalQuantityTonnes", 3000.0, qty, 0.001);
    }

    private static void assertEquals(String field, String expected, String actual) {
        if (actual == null || !actual.equals(expected)) {
            throw new AssertionError("Baseline mismatch on field '" + field + "': expected=" + expected + " actual=" + actual);
        }
    }

    private static void assertNumeric(String field, double expected, double actual, double tolerance) {
        if (Math.abs(actual - expected) > tolerance) {
            throw new AssertionError("Baseline mismatch on field '" + field + "': expected=" + expected + " actual=" + actual + " (tolerance=" + tolerance + ")");
        }
    }
}
