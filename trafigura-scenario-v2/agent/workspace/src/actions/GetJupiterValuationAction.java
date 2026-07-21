package actions;

import system.TradeValuation;

/** ACTION: Fetch valuation for the current trade from the external Jupiter system. */
public class GetJupiterValuationAction {
    public static TradeValuation run(ActionContext ctx) {
        TradeValuation valuation = ctx.system.getValuation(ctx.currentTrade.getTradeId());
        ctx.lastValuation = valuation;
        return valuation;
    }
}
