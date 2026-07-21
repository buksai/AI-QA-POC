package actions;

import system.Tranche;

/** ACTION: Add a shipment tranche to the current trade. */
public class AddTrancheAction {
    public static void run(ActionContext ctx, String shipmentMonth, double quantityTonnes,
                            String originPort, String destinationPort) {
        Tranche tranche = new Tranche(shipmentMonth, quantityTonnes, originPort, destinationPort);
        ctx.currentTrade.addTranche(tranche);
    }
}
