package actions;

import system.Trade;
import system.TradeCaptureSystem;
import system.TradeValuation;
import java.util.HashMap;
import java.util.Map;

/** Shared state passed between actions within one scenario run — holds the last created
 *  trade, last valuation fetched, etc. Mirrors how action chains share context in the
 *  real framework. */
public class ActionContext {
    public final TradeCaptureSystem system = new TradeCaptureSystem();
    public Trade currentTrade;
    public TradeValuation lastValuation;
    public final Map<String, Object> data = new HashMap<>();
}
