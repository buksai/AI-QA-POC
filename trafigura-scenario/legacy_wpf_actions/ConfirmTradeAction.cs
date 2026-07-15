// Legacy WPF UI action - part of the existing action library for the desktop client.
// Interacts with the WPF trade confirmation form.
using System.Windows.Automation;

public class ConfirmTradeAction
{
    public static void Run(AutomationElement mainWindow, string tradeId)
    {
        var tradeIdField = mainWindow.FindFirst(TreeScope.Descendants,
            new PropertyCondition(AutomationElement.AutomationIdProperty, "txtTradeId"));
        ((ValuePattern)tradeIdField.GetCurrentPattern(ValuePattern.Pattern)).SetValue(tradeId);

        var confirmButton = mainWindow.FindFirst(TreeScope.Descendants,
            new PropertyCondition(AutomationElement.AutomationIdProperty, "btnConfirmTrade"));
        ((InvokePattern)confirmButton.GetCurrentPattern(InvokePattern.Pattern)).Invoke();

        var statusLabel = mainWindow.FindFirst(TreeScope.Descendants,
            new PropertyCondition(AutomationElement.AutomationIdProperty, "lblTradeStatus"));
        string statusText = ((ValuePattern)statusLabel.GetCurrentPattern(ValuePattern.Pattern)).Current.Value;

        if (statusText != "CONFIRMED")
        {
            throw new System.Exception("Expected trade status CONFIRMED, got: " + statusText);
        }
    }
}
