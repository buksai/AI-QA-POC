package system;

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

    public void confirmTrade(String tradeId) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        t.setStatus(Trade.Status.CONFIRMED);
    }

    public TradeValuation getValuation(String tradeId) {
        Trade t = trades.get(tradeId);
        if (t == null) throw new IllegalArgumentException("Trade not found: " + tradeId);
        return jupiter.getValuation(t);
    }

    public Trade getTrade(String tradeId) {
        return trades.get(tradeId);
    }
}
