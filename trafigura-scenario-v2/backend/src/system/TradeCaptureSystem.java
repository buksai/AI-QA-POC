package system;

import java.util.Collection;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** The trade capture system under test — the client's in-house ERP-style application.
 *  Thread-safe: 50 concurrent scenarios can create/confirm/value/amend trades
 *  simultaneously without corrupting shared state. */
public class TradeCaptureSystem {
    private final ConcurrentHashMap<String, Trade> trades = new ConcurrentHashMap<>();
    private final JupiterValuationClient jupiter = new JupiterValuationClient();
    private final AtomicInteger nextId = new AtomicInteger(1);

    public Trade createTrade(String commodity, String counterparty) {
        String id = "TRD-" + String.format("%05d", nextId.getAndIncrement());
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
