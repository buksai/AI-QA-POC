package actions;

/**
 * ACTION: Amend an existing (confirmed) trade — change the total tonnage on
 * one of its tranches. Mirrors the client's mid-lifecycle amendment flow:
 * a trade doesn't just get created and forgotten; its quantity, counterparty,
 * or shipment details often change before settlement.
 */
public class AmendTradeAction {
    public static void run(ActionContext ctx, int trancheIndex, double newQuantityTonnes) {
        ctx.system.amendTrancheQuantity(ctx.currentTrade.getTradeId(), trancheIndex, newQuantityTonnes);
    }
}
