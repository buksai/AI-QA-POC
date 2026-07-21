package system;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

/** The trade capture system under test — the client's in-house ERP-style application. */
public class TradeCaptureSystem {
    private final Map<String, Trade> trades = new HashMap<>();
    private final JupiterValuationClient jupiter = new JupiterValuationClient();
    private int nextId = 1;

    public Trade createTrade(String commodity, String counterparty) {
        String id = "TRD-" + String.format("%05d", nextId++);
        Trade trade = new Trade(id, commodity, counterparty);
        trades.put(id, trade);
        return trade;
    }

    public void addTranche(String tradeId, String shipmentMonth, double quantityTonnes,
                            String originPort, String destinationPort) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        t.addTranche(new Tranche(shipmentMonth, quantityTonnes, originPort, destinationPort));
    }

    public Collection<Trade> allTrades() {
        return trades.values();
    }

    public JupiterValuationClient jupiterClient() {
        return jupiter;
    }

    public void confirmTrade(String tradeId) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        t.setStatus(Trade.Status.CONFIRMED);
    }

    public void amendTrancheQuantity(String tradeId, int trancheIndex, double newQuantityTonnes) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        if (t.getStatus() == Trade.Status.SETTLED) {
            throw new IllegalStateException("Cannot amend a settled trade: " + tradeId);
        }
        if (trancheIndex < 0 || trancheIndex >= t.getTranches().size()) {
            throw new IndexOutOfBoundsException("Tranche index out of range: " + trancheIndex);
        }
        t.getTranches().get(trancheIndex).setQuantityTonnes(newQuantityTonnes);
    }

    public TradeValuation getValuation(String tradeId) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        return jupiter.getValuation(t);
    }

    public TradeValuation getValuationForPricingDate(String tradeId, String pricingDate) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        return jupiter.getValuationForPricingDate(t, pricingDate);
    }

    public Trade getTrade(String tradeId) {
        return trades.get(tradeId);
    }
}
