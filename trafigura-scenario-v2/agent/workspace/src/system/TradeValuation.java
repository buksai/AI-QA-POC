package system;

/** Result of a valuation call to the external Jupiter pricing system. */
public class TradeValuation {
    private final double pricePerTonneUsd;
    private final double totalValueUsd;

    public TradeValuation(double pricePerTonneUsd, double totalValueUsd) {
        this.pricePerTonneUsd = pricePerTonneUsd;
        this.totalValueUsd = totalValueUsd;
    }

    public double getPricePerTonneUsd() { return pricePerTonneUsd; }
    public double getTotalValueUsd() { return totalValueUsd; }
}
