package actions;

/** ACTION: Confirm the current trade (moves it from DRAFT to CONFIRMED). */
public class ConfirmTradeAction {
    public static void run(ActionContext ctx) {
        ctx.system.confirmTrade(ctx.currentTrade.getTradeId());
    }
}
