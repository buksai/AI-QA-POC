package api;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Minimal hand-rolled JSON writer/reader — no external dependency available
 *  in this environment, and the API surface here is small and fixed, so a
 *  tiny purpose-built codec is more honest than pretending to use a real
 *  JSON library. */
public class Json {

    public static String obj(Object... kvPairs) {
        StringBuilder sb = new StringBuilder("{");
        for (int i = 0; i < kvPairs.length; i += 2) {
            if (i > 0) sb.append(",");
            sb.append("\"").append(kvPairs[i]).append("\":").append(value(kvPairs[i + 1]));
        }
        sb.append("}");
        return sb.toString();
    }

    public static String arr(List<String> rawJsonObjects) {
        return "[" + String.join(",", rawJsonObjects) + "]";
    }

    private static String value(Object v) {
        if (v == null) return "null";
        if (v instanceof Number || v instanceof Boolean) return v.toString();
        if (v instanceof RawJson) return ((RawJson) v).json;
        return "\"" + v.toString().replace("\"", "\\\"") + "\"";
    }

    public static RawJson raw(String json) { return new RawJson(json); }

    public static class RawJson {
        final String json;
        RawJson(String json) { this.json = json; }
    }

    /** Very small flat-object parser: handles {"key": "string"} and
     *  {"key": 123.45} pairs only, sufficient for this API's request bodies. */
    public static Map<String, String> parseFlat(String body) {
        Map<String, String> result = new LinkedHashMap<>();
        if (body == null) return result;
        body = body.trim();
        if (body.startsWith("{")) body = body.substring(1);
        if (body.endsWith("}")) body = body.substring(0, body.length() - 1);
        int i = 0;
        while (i < body.length()) {
            int keyStart = body.indexOf('"', i);
            if (keyStart < 0) break;
            int keyEnd = body.indexOf('"', keyStart + 1);
            String key = body.substring(keyStart + 1, keyEnd);
            int colon = body.indexOf(':', keyEnd);
            int valStart = colon + 1;
            while (valStart < body.length() && body.charAt(valStart) == ' ') valStart++;
            String val;
            int nextComma;
            if (body.charAt(valStart) == '"') {
                int valEnd = body.indexOf('"', valStart + 1);
                val = body.substring(valStart + 1, valEnd);
                nextComma = body.indexOf(',', valEnd);
            } else {
                nextComma = body.indexOf(',', valStart);
                int end = nextComma < 0 ? body.length() : nextComma;
                val = body.substring(valStart, end).trim();
            }
            result.put(key, val);
            i = nextComma < 0 ? body.length() : nextComma + 1;
        }
        return result;
    }
}
