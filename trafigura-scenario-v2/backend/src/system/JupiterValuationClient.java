package system;

/**
 * Mock client for the external Jupiter pricing/valuation system.
 *
 * THREE live runtime toggles (not baked into committed source) - so a
 * clean Reset genuinely means a fully healthy suite (54/0), and
 * "Break the suite" is a single, real, live regression event applied on
 * top of that healthy baseline, simulating a bad release that:
 *   1. Enables a 1.5% port handling fee (handlingFeeEnabled)
 *   2. Introduces a market-data lag on the release branch
 *      (pricingDataAvailableFrom advances forward)
 *   3. SILENTLY REMOVES the volume-discount feature required by
 *      REQ-114 (volumeDiscountEnabled flips to false) - this is the
 *      genuine product defect: an approved, existing business requirement
 *      that the "bad release" violates. See knowledge_base/requirements.json
 *      for REQ-114's text.
 *
 * Before "Break the suite": all three are in their healthy default state,
 * and the full scenario suite passes. This is a single controlled event,
 * not three unrelated bugs - representing one bad release that regressed
 * multiple things at once, which is realistic for a weekly regression run.
 */
public class JupiterValuationClient {

    private static final double COPPER_CONCENTRATE_PRICE_PER_TONNE = 4250.00;
    private static final double HANDLING_FEE_RATE = 0.015; // 1.5% port handling fee (JIRA-4821)
    private static final double VOLUME_DISCOUNT_RATE = 0.03; // REQ-114: 3% discount for trades >= 5,000t
    private static final double VOLUME_DISCOUNT_THRESHOLD_TONNES = 5000.0;

    // Default: early enough that every committed scenario's pricing date
    // (2026-01-15 onward) has market data. "Break the suite" advances this.
    private static final String DEFAULT_PRICING_DATA_AVAILABLE_FROM = "2025-01-01";

    private volatile boolean handlingFeeEnabled = false;
    private volatile String pricingDataAvailableFrom = DEFAULT_PRICING_DATA_AVAILABLE_FROM;
    private volatile boolean volumeDiscountEnabled = true; // REQ-114 honored by default

    public void setHandlingFeeEnabled(boolean enabled) { this.handlingFeeEnabled = enabled; }
    public boolean isHandlingFeeEnabled() { return handlingFeeEnabled; }

    public void setPricingDataCutoff(String cutoffDate) { this.pricingDataAvailableFrom = cutoffDate; }
    public String getPricingDataCutoff() { return pricingDataAvailableFrom; }
    public void resetPricingDataCutoff() { this.pricingDataAvailableFrom = DEFAULT_PRICING_DATA_AVAILABLE_FROM; }

    public void setVolumeDiscountEnabled(boolean enabled) { this.volumeDiscountEnabled = enabled; }
    public boolean isVolumeDiscountEnabled() { return volumeDiscountEnabled; }

    public TradeValuation getValuation(Trade trade) {
        double qty = trade.totalQuantityTonnes();
        double subtotal = qty * COPPER_CONCENTRATE_PRICE_PER_TONNE;
        if (volumeDiscountEnabled && qty >= VOLUME_DISCOUNT_THRESHOLD_TONNES) {
            subtotal = subtotal * (1 - VOLUME_DISCOUNT_RATE);
        }
        double total = handlingFeeEnabled ? subtotal * (1 + HANDLING_FEE_RATE) : subtotal;
        return new TradeValuation(COPPER_CONCENTRATE_PRICE_PER_TONNE, total);
    }

    /** Valuation that requires market data for the given pricing date. */
    public TradeValuation getValuationForPricingDate(Trade trade, String pricingDate) {
        if (pricingDate != null && pricingDate.compareTo(pricingDataAvailableFrom) < 0) {
            throw new IllegalStateException("No pricing data found for date " + pricingDate);
        }
        return getValuation(trade);
    }
}
