package system;

/**
 * Mock client for the external Jupiter pricing/valuation system.
 *
 * Two real, demo-relevant behaviours:
 *  1. handlingFeeEnabled — runtime toggle for a 1.5% port handling fee.
 *  2. pricing-date availability — Jupiter only has market data on or after
 *     a cutoff date. Requesting a valuation for a pricing date before the
 *     cutoff throws "No pricing data found for date ..." — exactly the
 *     release-environment failure Wagner's team hits, where a scenario's
 *     hard-coded date has no market data in that environment.
 */
public class JupiterValuationClient {

    private static final double COPPER_CONCENTRATE_PRICE_PER_TONNE = 4250.00;
    private static final double HANDLING_FEE_RATE = 0.015; // 1.5% port handling fee (JIRA-4821)

    // Market data in this (release) environment only exists from Feb 2026 onward.
    private static final String PRICING_DATA_AVAILABLE_FROM = "2026-02-01";

    private volatile boolean handlingFeeEnabled = false;

    public void setHandlingFeeEnabled(boolean enabled) { this.handlingFeeEnabled = enabled; }
    public boolean isHandlingFeeEnabled() { return handlingFeeEnabled; }

    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double subtotal = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        double total = handlingFeeEnabled ? subtotal * (1 + HANDLING_FEE_RATE) : subtotal;
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }

    /** Valuation that requires market data for the given pricing date. */
    public TradeValuation getValuationForPricingDate(Trade trade, String pricingDate) {
        if (pricingDate != null && pricingDate.compareTo(PRICING_DATA_AVAILABLE_FROM) < 0) {
            throw new IllegalStateException("No pricing data found for date " + pricingDate);
        }
        return getValuation(trade);
    }
}
