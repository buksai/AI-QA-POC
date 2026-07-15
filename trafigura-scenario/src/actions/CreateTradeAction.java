package actions;

import system.Trade;

/** ACTION: Create a new trade in the system. */
public class CreateTradeAction {
    public static Trade run(ActionContext ctx, String commodity, String counterparty) {
        Trade trade = ctx.system.createTrade(commodity, counterparty);
        ctx.currentTrade = trade;
        return trade;
    }
}
