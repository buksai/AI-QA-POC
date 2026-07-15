package system;

/**
 * Mock client for the external Jupiter pricing/valuation system.
 * In production this calls out to Jupiter over the network; here it's a
 * local stand-in so the scenario is fully self-contained and runnable.
 */
public class JupiterValuationClient {

    private static final double COPPER_CONCENTRATE_PRICE_PER_TONNE = 4250.00;

    private static final double HANDLING_FEE_RATE = 0.015; // 1.5% port handling fee, added per Ops request JIRA-4821

    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double subtotal = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        double total = subtotal * (1 + HANDLING_FEE_RATE);
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }
}
