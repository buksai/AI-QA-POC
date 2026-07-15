package scenarios;

import actions.*;
import system.Trade;
import system.TradeValuation;

/**
 * END-TO-END REGRESSION SCENARIO
 * Business flow: create a copper concentrate trade, schedule a shipment tranche
 * from Colombia to China, confirm the trade, then verify the Jupiter valuation
 * matches the recorded baseline.
 *
 * This is the shape of scenario used for aggression [regression] testing —
 * built entirely from reusable actions, with baseline comparison as the
 * final evidence check.
 */
public class CopperConcentrateTradeScenario {

    public static void testCreateAndValueCopperConcentrateTrade() {
        ActionContext ctx = new ActionContext();

        // Step 1: create the trade
        Trade trade = CreateTradeAction.run(ctx, "Copper Concentrate", "Southern Metals Corp");

        // Step 2: schedule one shipment tranche (2,000 tonnes, Colombia -> China)
        AddTrancheAction.run(ctx, "2026-09", 2000.0, "Buenaventura", "Qingdao");

        // Step 3: confirm the trade
        ConfirmTradeAction.run(ctx);

        // Step 4: get valuation from Jupiter
        TradeValuation valuation = GetJupiterValuationAction.run(ctx);

        // Step 5: compare against recorded baseline evidence
        CompareBaselineAction.run("trade.status", trade.getStatus().toString(), "CONFIRMED");
        CompareBaselineAction.runNumeric("trade.totalQuantityTonnes", trade.totalQuantityTonnes(), 2000.0, 0.001);
        CompareBaselineAction.runNumeric("valuation.totalValueUsd", valuation.getTotalValueUsd(), 8500000.00, 0.01);
    }

    public static void testMultiTrancheTradeQuantity() {
        ActionContext ctx = new ActionContext();

        Trade trade = CreateTradeAction.run(ctx, "Copper Concentrate", "Andes Mining SA");
        AddTrancheAction.run(ctx, "2026-08", 1500.0, "Buenaventura", "Qingdao");
        AddTrancheAction.run(ctx, "2026-11", 1500.0, "Buenaventura", "Qingdao");
        ConfirmTradeAction.run(ctx);

        CompareBaselineAction.runNumeric("trade.totalQuantityTonnes", trade.totalQuantityTonnes(), 3000.0, 0.001);
    }
}
