package system;

import java.util.ArrayList;
import java.util.List;

/** Core trade entity in the trade capture system (mirrors the client's ERP-style model). */
public class Trade {
    public enum Status { DRAFT, CONFIRMED, SETTLED }

    private final String tradeId;
    private final String commodity;
    private final String counterparty;
    private Status status;
    private final List<Tranche> tranches = new ArrayList<>();

    public Trade(String tradeId, String commodity, String counterparty) {
        this.tradeId = tradeId;
        this.commodity = commodity;
        this.counterparty = counterparty;
        this.status = Status.DRAFT;
    }

    public String getTradeId() { return tradeId; }
    public String getCommodity() { return commodity; }
    public String getCounterparty() { return counterparty; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public List<Tranche> getTranches() { return tranches; }
    public void addTranche(Tranche t) { tranches.add(t); }

    public double totalQuantityTonnes() {
        double sum = 0;
        for (Tranche t : tranches) sum += t.getQuantityTonnes();
        return sum;
    }
}
