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

    /**
     * Amendment scenario: create and confirm a trade, then amend the tranche
     * quantity mid-lifecycle (a common real-world event — e.g. the counterparty
     * revises the delivery amount). Re-fetch the Jupiter valuation and verify
     * the new baseline reflects the amended quantity.
     */
    public static void testAmendTradeQuantityAndRevalue() {
        ActionContext ctx = new ActionContext();

        // Initial trade: 2000 tonnes copper concentrate, Colombia -> China
        Trade trade = CreateTradeAction.run(ctx, "Copper Concentrate", "Southern Metals Corp");
        AddTrancheAction.run(ctx, "2026-09", 2000.0, "Buenaventura", "Qingdao");
        ConfirmTradeAction.run(ctx);

        // Counterparty amends the delivery: uprated from 2000 to 2500 tonnes
        AmendTradeAction.run(ctx, 0, 2500.0);

        // Re-fetch valuation from Jupiter — should reflect the amended quantity
        TradeValuation revaluation = GetJupiterValuationAction.run(ctx);

        // Baseline evidence checks against the amended trade
        CompareBaselineAction.run("trade.status", trade.getStatus().toString(), "CONFIRMED");
        CompareBaselineAction.runNumeric("trade.totalQuantityTonnes", trade.totalQuantityTonnes(), 2500.0, 0.001);
        CompareBaselineAction.runNumeric("revaluation.totalValueUsd", revaluation.getTotalValueUsd(), 10625000.00, 0.01);
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
