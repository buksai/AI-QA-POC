import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

/**
 * Minimal, dependency-free test runner. Scans the given scenario classes for
 * public static methods starting with "test", invokes each, and reports
 * pass/fail in a pytest-style summary. No JUnit/Maven required — keeps the
 * POC runnable with nothing but a JDK.
 */
public class TestRunner {
    public static void main(String[] args) throws Exception {
        List<Class<?>> scenarioClasses = new ArrayList<>();
        scenarioClasses.add(Class.forName("scenarios.CopperConcentrateTradeScenario"));
        scenarioClasses.add(Class.forName("scenarios.TitanReleaseScenario"));

        int passed = 0;
        int failed = 0;
        List<String> failures = new ArrayList<>();

        for (Class<?> cls : scenarioClasses) {
            for (Method m : cls.getMethods()) {
                if (m.getName().startsWith("test")) {
                    String fqName = cls.getSimpleName() + "." + m.getName();
                    try {
                        m.invoke(null);
                        System.out.println("PASSED  " + fqName);
                        passed++;
                    } catch (Exception e) {
                        Throwable cause = e.getCause() != null ? e.getCause() : e;
                        System.out.println("FAILED  " + fqName);
                        System.out.println("        " + cause.getClass().getSimpleName() + ": " + cause.getMessage());
                        failures.add(fqName + ": " + cause.getClass().getSimpleName() + ": " + cause.getMessage());
                        failed++;
                    }
                }
            }
        }

        System.out.println();
        System.out.println(passed + " passed, " + failed + " failed");
        if (failed > 0) {
            System.exit(1);
        }
    }
}
