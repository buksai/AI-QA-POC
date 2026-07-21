package system;

/**
 * Mock client for the external Jupiter pricing/valuation system.
 * In production this calls out to Jupiter over the network; here it's a
 * local stand-in so the scenario is fully self-contained and runnable.
 *
 * handlingFeeEnabled is a REAL runtime toggle (not a code edit + recompile) —
 * flipping it via the admin API immediately changes what every caller of
 * this class sees: the legacy UI, the web UI, and the agent's HTTP-based
 * regression tests are all reading from this one live instance.
 */
public class JupiterValuationClient {

    private static final double COPPER_CONCENTRATE_PRICE_PER_TONNE = 4250.00;
    private static final double HANDLING_FEE_RATE = 0.015; // 1.5% port handling fee (JIRA-4821)

    private volatile boolean handlingFeeEnabled = false;

    public void setHandlingFeeEnabled(boolean enabled) {
        this.handlingFeeEnabled = enabled;
    }

    public boolean isHandlingFeeEnabled() {
        return handlingFeeEnabled;
    }

    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double subtotal = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        double total = handlingFeeEnabled ? subtotal * (1 + HANDLING_FEE_RATE) : subtotal;
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }
}
