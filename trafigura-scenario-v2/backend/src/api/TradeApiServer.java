package api;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import system.Trade;
import system.TradeCaptureSystem;
import system.TradeValuation;
import system.Tranche;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Real HTTP backend for the trade capture system — no mocked responses.
 * Both the legacy-style UI and the new web UI call this same server, proving
 * the business logic is genuinely shared and only the front-end changes
 * during the WPF -> web migration.
 *
 * Uses only the JDK's built-in com.sun.net.httpserver — no external
 * dependencies (Maven Central isn't reachable from this environment).
 */
public class TradeApiServer {

    private static final TradeCaptureSystem SYSTEM = new TradeCaptureSystem();

    public static void main(String[] args) throws IOException {
        int port = args.length > 0 ? Integer.parseInt(args[0]) : 5100;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/api/trades", new TradesHandler());
        server.createContext("/api/health", exchange -> respond(exchange, 200, Json.obj("status", "ok")));
        server.createContext("/api/admin/handling-fee", new HandlingFeeHandler());

        server.setExecutor(null);
        server.start();
        System.out.println("TradeApiServer listening on http://127.0.0.1:" + port);
    }

    static class HandlingFeeHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
            exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
            String method = exchange.getRequestMethod();
            System.out.println(java.time.LocalTime.now().withNano(0) + "  " + method + " /api/admin/handling-fee");
            if (method.equals("OPTIONS")) { exchange.sendResponseHeaders(204, -1); return; }

            if (method.equals("GET")) {
                respond(exchange, 200, Json.obj("handlingFeeEnabled", SYSTEM.jupiterClient().isHandlingFeeEnabled()));
                return;
            }
            if (method.equals("POST")) {
                String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
                Map<String, String> f = Json.parseFlat(body);
                boolean enabled = "true".equalsIgnoreCase(f.getOrDefault("enabled", "false"));
                SYSTEM.jupiterClient().setHandlingFeeEnabled(enabled);
                respond(exchange, 200, Json.obj("handlingFeeEnabled", enabled));
                return;
            }
            respond(exchange, 404, Json.obj("error", "not found"));
        }
    }

    static class TradesHandler implements HttpHandler {
        // Matches: /api/trades, /api/trades/{id}, /api/trades/{id}/tranches,
        // /api/trades/{id}/confirm, /api/trades/{id}/valuation,
        // /api/trades/{id}/tranches/{idx}/amend
        private static final Pattern TRADE_ID = Pattern.compile("^/api/trades/([^/]+)$");
        private static final Pattern TRANCHES = Pattern.compile("^/api/trades/([^/]+)/tranches$");
        private static final Pattern CONFIRM = Pattern.compile("^/api/trades/([^/]+)/confirm$");
        private static final Pattern VALUATION = Pattern.compile("^/api/trades/([^/]+)/valuation$");
        private static final Pattern AMEND = Pattern.compile("^/api/trades/([^/]+)/tranches/(\\d+)/amend$");

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            String method = exchange.getRequestMethod();
            System.out.println(java.time.LocalTime.now().withNano(0) + "  " + method + " " + path);

            // CORS so the static HTML UIs (opened from file:// or another port) can call this
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
            exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
            if (method.equals("OPTIONS")) {
                exchange.sendResponseHeaders(204, -1);
                return;
            }

            String body = readBody(exchange);

            try {
                if (path.equals("/api/trades") && method.equals("POST")) {
                    handleCreateTrade(exchange, body);
                } else if (path.equals("/api/trades") && method.equals("GET")) {
                    handleListTrades(exchange);
                } else if (TRANCHES.matcher(path).matches() && method.equals("POST")) {
                    handleAddTranche(exchange, TRANCHES.matcher(path), body);
                } else if (CONFIRM.matcher(path).matches() && method.equals("POST")) {
                    handleConfirm(exchange, CONFIRM.matcher(path));
                } else if (VALUATION.matcher(path).matches() && method.equals("GET")) {
                    handleValuation(exchange, VALUATION.matcher(path));
                } else if (AMEND.matcher(path).matches() && method.equals("POST")) {
                    handleAmend(exchange, AMEND.matcher(path), body);
                } else if (TRADE_ID.matcher(path).matches() && method.equals("GET")) {
                    handleGetTrade(exchange, TRADE_ID.matcher(path));
                } else {
                    respond(exchange, 404, Json.obj("error", "not found"));
                }
            } catch (Exception e) {
                respond(exchange, 400, Json.obj("error", e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage()));
            }
        }

        private void handleCreateTrade(HttpExchange exchange, String body) throws IOException {
            Map<String, String> fields = Json.parseFlat(body);
            Trade trade = SYSTEM.createTrade(fields.get("commodity"), fields.get("counterparty"));
            respond(exchange, 201, tradeJson(trade));
        }

        private void handleListTrades(HttpExchange exchange) throws IOException {
            List<String> items = new ArrayList<>();
            for (Trade t : SYSTEM.allTrades()) items.add(tradeJson(t));
            respond(exchange, 200, Json.raw(Json.arr(items)).json);
        }

        private void handleAddTranche(HttpExchange exchange, Matcher m, String body) throws IOException {
            m.matches();
            String tradeId = m.group(1);
            Map<String, String> f = Json.parseFlat(body);
            SYSTEM.addTranche(tradeId, f.get("shipmentMonth"),
                    Double.parseDouble(f.get("quantityTonnes")), f.get("originPort"), f.get("destinationPort"));
            respond(exchange, 201, tradeJson(SYSTEM.getTrade(tradeId)));
        }

        private void handleConfirm(HttpExchange exchange, Matcher m) throws IOException {
            m.matches();
            String tradeId = m.group(1);
            SYSTEM.confirmTrade(tradeId);
            respond(exchange, 200, tradeJson(SYSTEM.getTrade(tradeId)));
        }

        private void handleValuation(HttpExchange exchange, Matcher m) throws IOException {
            m.matches();
            String tradeId = m.group(1);
            String query = exchange.getRequestURI().getQuery();
            String pricingDate = null;
            if (query != null && query.startsWith("pricingDate=")) {
                pricingDate = query.substring("pricingDate=".length());
            }
            TradeValuation v = (pricingDate != null)
                    ? SYSTEM.getValuationForPricingDate(tradeId, pricingDate)
                    : SYSTEM.getValuation(tradeId);
            respond(exchange, 200, Json.obj(
                    "pricePerTonneUsd", v.getPricePerTonneUsd(),
                    "totalValueUsd", v.getTotalValueUsd()
            ));
        }

        private void handleAmend(HttpExchange exchange, Matcher m, String body) throws IOException {
            m.matches();
            String tradeId = m.group(1);
            int trancheIdx = Integer.parseInt(m.group(2));
            Map<String, String> f = Json.parseFlat(body);
            SYSTEM.amendTrancheQuantity(tradeId, trancheIdx, Double.parseDouble(f.get("quantityTonnes")));
            respond(exchange, 200, tradeJson(SYSTEM.getTrade(tradeId)));
        }

        private void handleGetTrade(HttpExchange exchange, Matcher m) throws IOException {
            m.matches();
            String tradeId = m.group(1);
            Trade t = SYSTEM.getTrade(tradeId);
            if (t == null) { respond(exchange, 404, Json.obj("error", "trade not found")); return; }
            respond(exchange, 200, tradeJson(t));
        }

        private String tradeJson(Trade t) {
            List<String> tranches = new ArrayList<>();
            int idx = 0;
            for (Tranche tr : t.getTranches()) {
                tranches.add(Json.obj(
                        "index", idx++,
                        "shipmentMonth", tr.getShipmentMonth(),
                        "quantityTonnes", tr.getQuantityTonnes(),
                        "originPort", tr.getOriginPort(),
                        "destinationPort", tr.getDestinationPort()
                ));
            }
            return Json.obj(
                    "tradeId", t.getTradeId(),
                    "commodity", t.getCommodity(),
                    "counterparty", t.getCounterparty(),
                    "status", t.getStatus().toString(),
                    "totalQuantityTonnes", t.totalQuantityTonnes(),
                    "tranches", Json.raw(Json.arr(tranches))
            );
        }
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        return new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
    }

    private static void respond(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
