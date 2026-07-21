import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.io.File;
import java.io.FilenameFilter;

/**
 * Concurrent test runner. Auto-discovers every scenario class under
 * src/scenarios/, then executes ALL test methods truly in parallel using a
 * fixed-size worker pool (default 50) — real threads, real concurrent HTTP
 * calls against the live backend, not simulated timers. Reports live
 * per-test results (with worker thread name, proving genuine concurrency),
 * then a structured final summary.
 */
public class TestRunner {

    public static void main(String[] args) throws Exception {
        int poolSize = args.length > 0 ? Integer.parseInt(args[0]) : 50;

        List<Class<?>> scenarioClasses = discoverScenarioClasses();

        // Flatten to individual (class, method) test units
        List<Object[]> testUnits = new ArrayList<>();
        for (Class<?> cls : scenarioClasses) {
            for (Method m : cls.getMethods()) {
                if (m.getName().startsWith("test")) {
                    testUnits.add(new Object[]{cls, m});
                }
            }
        }

        int total = testUnits.size();
        long startTime = System.currentTimeMillis();
        System.out.println("=== CONCURRENT EXECUTION: " + total + " scenarios, " + poolSize + " workers ===");
        System.out.println("start_time=" + startTime);

        ExecutorService pool = Executors.newFixedThreadPool(poolSize);
        AtomicInteger passed = new AtomicInteger(0);
        AtomicInteger failed = new AtomicInteger(0);
        List<Future<String>> futures = new ArrayList<>();
        List<String> failureLines = Collections.synchronizedList(new ArrayList<>());

        for (Object[] unit : testUnits) {
            Class<?> cls = (Class<?>) unit[0];
            Method m = (Method) unit[1];
            futures.add(pool.submit(() -> {
                String fqName = cls.getSimpleName() + "." + m.getName();
                String worker = Thread.currentThread().getName();
                try {
                    m.invoke(null);
                    passed.incrementAndGet();
                    String line = "PASSED  [" + worker + "] " + fqName;
                    System.out.println(line);
                    return line;
                } catch (Exception e) {
                    Throwable cause = e.getCause() != null ? e.getCause() : e;
                    failed.incrementAndGet();
                    String line = "FAILED  [" + worker + "] " + fqName + "\n        "
                            + cause.getClass().getSimpleName() + ": " + cause.getMessage();
                    System.out.println(line);
                    failureLines.add(fqName + ": " + cause.getClass().getSimpleName() + ": " + cause.getMessage());
                    return line;
                }
            }));
        }

        for (Future<String> f : futures) f.get();
        pool.shutdown();

        long durationMs = System.currentTimeMillis() - startTime;

        System.out.println();
        System.out.println("=== SUMMARY ===");
        System.out.println("total_scenarios=" + total);
        System.out.println("workers=" + poolSize);
        System.out.println("duration_ms=" + durationMs);
        System.out.println(passed.get() + " passed, " + failed.get() + " failed");

        if (failed.get() > 0) System.exit(1);
    }

    private static List<Class<?>> discoverScenarioClasses() throws Exception {
        File dir = new File("src/scenarios");
        String[] files = dir.list((d, name) -> name.endsWith(".java"));
        List<Class<?>> classes = new ArrayList<>();
        if (files == null) return classes;
        java.util.Arrays.sort(files);
        for (String f : files) {
            String className = "scenarios." + f.replace(".java", "");
            classes.add(Class.forName(className));
        }
        return classes;
    }
}
