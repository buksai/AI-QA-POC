package system;

/** A shipment tranche of a trade (e.g. one vessel load within a year-long delivery schedule). */
public class Tranche {
    private final String shipmentMonth;
    private final double quantityTonnes;
    private final String originPort;
    private final String destinationPort;

    public Tranche(String shipmentMonth, double quantityTonnes, String originPort, String destinationPort) {
        this.shipmentMonth = shipmentMonth;
        this.quantityTonnes = quantityTonnes;
        this.originPort = originPort;
        this.destinationPort = destinationPort;
    }

    public String getShipmentMonth() { return shipmentMonth; }
    public double getQuantityTonnes() { return quantityTonnes; }
    public String getOriginPort() { return originPort; }
    public String getDestinationPort() { return destinationPort; }
}
