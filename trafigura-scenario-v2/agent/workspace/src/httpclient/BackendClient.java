package httpclient;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Real HTTP client for the live trade capture backend. Uses only java.net.http
 * (built into the JDK) — no external dependencies. This is what makes the
 * agent's regression suite hit the SAME running system as the legacy and web
 * UIs, instead of a private in-memory copy: one backend, one source of truth.
 */
public class BackendClient {
    private static final String BASE = "http://127.0.0.1:5100/api";
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build();

    // Thread-safe registry of every trade ID this process has created, for
    // concurrency proof: verifying zero ID collisions across genuinely
    // concurrent scenario execution, checked against the SAME running
    // backend process (not a fresh restart).
    private static final java.util.concurrent.ConcurrentLinkedQueue<String> createdTradeIds =
            new java.util.concurrent.ConcurrentLinkedQueue<>();

    public static java.util.List<String> getCreatedTradeIds() {
        return new java.util.ArrayList<>(createdTradeIds);
    }

    public String createTrade(String commodity, String counterparty) {
        String body = "{\"commodity\":\"" + commodity + "\",\"counterparty\":\"" + counterparty + "\"}";
        String resp = post(BASE + "/trades", body);
        String tradeId = extract(resp, "tradeId");
        createdTradeIds.add(tradeId);
        return tradeId;
    }

    public void addTranche(String tradeId, String month, double qty, String origin, String dest) {
        String body = String.format(
                "{\"shipmentMonth\":\"%s\",\"quantityTonnes\":%s,\"originPort\":\"%s\",\"destinationPort\":\"%s\"}",
                month, qty, origin, dest);
        post(BASE + "/trades/" + tradeId + "/tranches", body);
    }

    public void confirmTrade(String tradeId) {
        post(BASE + "/trades/" + tradeId + "/confirm", "{}");
    }

    public void amendTranche(String tradeId, int index, double newQty) {
        post(BASE + "/trades/" + tradeId + "/tranches/" + index + "/amend",
                "{\"quantityTonnes\":" + newQty + "}");
    }

    public double getValuationTotalUsd(String tradeId) {
        String resp = get(BASE + "/trades/" + tradeId + "/valuation");
        return Double.parseDouble(extract(resp, "totalValueUsd"));
    }

    public double getValuationForPricingDate(String tradeId, String pricingDate) {
        String resp = get(BASE + "/trades/" + tradeId + "/valuation?pricingDate=" + pricingDate);
        return Double.parseDouble(extract(resp, "totalValueUsd"));
    }

    public String getTradeStatus(String tradeId) {
        String resp = get(BASE + "/trades/" + tradeId);
        return extract(resp, "status");
    }

    public double getTradeTotalQuantity(String tradeId) {
        String resp = get(BASE + "/trades/" + tradeId);
        return Double.parseDouble(extract(resp, "totalQuantityTonnes"));
    }

    private String post(String url, String body) {
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() >= 400) {
                throw new RuntimeException("Backend error " + resp.statusCode() + ": " + resp.body());
            }
            return resp.body();
        } catch (IOException | InterruptedException e) {
            throw new RuntimeException(
                "Could not reach trade capture backend at " + BASE +
                " - is it running? (java -cp out api.TradeApiServer 5100)", e);
        }
    }

    private String get(String url) {
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(url)).GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() >= 400) {
                throw new RuntimeException("Backend error " + resp.statusCode() + ": " + resp.body());
            }
            return resp.body();
        } catch (IOException | InterruptedException e) {
            throw new RuntimeException(
                "Could not reach trade capture backend at " + BASE +
                " - is it running? (java -cp out api.TradeApiServer 5100)", e);
        }
    }

    // Minimal flat-JSON field extractor (string or number values) - matches
    // the same small JSON surface the backend itself hand-rolls.
    private String extract(String json, String key) {
        Pattern p = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*(\"([^\"]*)\"|[-0-9.eE]+)");
        Matcher m = p.matcher(json);
        if (!m.find()) throw new RuntimeException("Field '" + key + "' not found in response: " + json);
        return m.group(2) != null ? m.group(2) : m.group(1);
    }
}
