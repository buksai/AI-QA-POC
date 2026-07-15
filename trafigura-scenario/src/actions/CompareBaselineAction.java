package actions;

/** ACTION: Compare an actual value against the recorded baseline value for this scenario.
 *  This is the core "evidence" check pattern used across regression scenarios. */
public class CompareBaselineAction {
    public static void run(String fieldName, Object actual, Object expectedBaseline) {
        if (actual == null || !actual.equals(expectedBaseline)) {
            throw new AssertionError(
                "Baseline mismatch on field '" + fieldName + "': " +
                "expected=" + expectedBaseline + " actual=" + actual
            );
        }
    }

    public static void runNumeric(String fieldName, double actual, double expectedBaseline, double tolerance) {
        if (Math.abs(actual - expectedBaseline) > tolerance) {
            throw new AssertionError(
                "Baseline mismatch on field '" + fieldName + "': " +
                "expected=" + expectedBaseline + " actual=" + actual +
                " (tolerance=" + tolerance + ")"
            );
        }
    }
}
