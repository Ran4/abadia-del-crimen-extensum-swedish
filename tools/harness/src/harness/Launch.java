package harness;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Bootstrap for the text-rendering harness.
 *
 * Builds a class loader whose search order is
 *   [harness game-side classes (package abadia)] , [--res directory overlay] , [--jar]
 * so that the game's own classes come from an arbitrary jar and every resource the game asks
 * for as "/res/NAME" is taken from the --res directory when it exists there, otherwise from
 * the jar. The parent loader is the platform/extension loader, so nothing named abadia.* can
 * leak in from the outer class path.
 *
 * Usage: java -Djava.awt.headless=true -cp build/launcher harness.Launch
 *            --harness-classes build/gameside --jar GAME.jar [--res RESDIR] [harness args...]
 */
public final class Launch {

    /** Overlays a directory on top of the jar for resource names starting with "res/". */
    static final class OverlayLoader extends URLClassLoader {
        final File resDir;
        final Map<String, String> used = new LinkedHashMap<>();

        OverlayLoader(URL[] urls, ClassLoader parent, File resDir) {
            super(urls, parent);
            this.resDir = resDir;
        }

        @Override
        public URL getResource(String name) {
            String key = name.startsWith("/") ? name.substring(1) : name;
            if (resDir != null && key.startsWith("res/")) {
                File file = new File(resDir, key.substring(4));
                if (file.isFile()) {
                    try {
                        URL url = file.toURI().toURL();
                        used.put(key, url.toString());
                        return url;
                    } catch (IOException ex) {
                        throw new RuntimeException(ex);
                    }
                }
            }
            URL url = super.getResource(name);
            if (key.startsWith("res/")) {
                used.put(key, url == null ? "NOT FOUND" : url.toString());
            }
            return url;
        }
    }

    public static void main(String[] args) throws Exception {
        if (!"true".equals(System.getProperty("java.awt.headless"))) {
            System.err.println("refusing to run: pass -Djava.awt.headless=true");
            System.exit(1);
        }
        String harnessClasses = null;
        String jar = null;
        String res = null;
        List<String> rest = new ArrayList<>();
        for (int idx = 0; idx < args.length; idx++) {
            String arg = args[idx];
            if (arg.equals("--harness-classes")) {
                harnessClasses = args[++idx];
            } else if (arg.equals("--jar")) {
                jar = args[++idx];
            } else if (arg.equals("--res")) {
                res = args[++idx];
            } else {
                rest.add(arg);
            }
        }
        if (harnessClasses == null || jar == null) {
            System.err.println("usage: harness.Launch --harness-classes DIR --jar GAME.jar [--res RESDIR] ...");
            System.exit(1);
        }
        File jarFile = new File(jar).getAbsoluteFile();
        File hcDir = new File(harnessClasses).getAbsoluteFile();
        File resDir = res == null ? null : new File(res).getAbsoluteFile();
        if (!jarFile.isFile()) {
            System.err.println("no such jar: " + jarFile);
            System.exit(1);
        }
        if (resDir != null && !resDir.isDirectory()) {
            System.err.println("no such res directory: " + resDir);
            System.exit(1);
        }
        URL[] urls = {hcDir.toURI().toURL(), jarFile.toURI().toURL()};
        OverlayLoader loader = new OverlayLoader(urls, ClassLoader.getSystemClassLoader().getParent(), resDir);
        Thread.currentThread().setContextClassLoader(loader);

        Class<?> harness = Class.forName("abadia.TextHarness", true, loader);
        // Sanity: the game classes must come from the given jar, the harness from its own dir.
        Class<?> game = Class.forName("abadia.j", false, loader);
        String gameSrc = String.valueOf(game.getProtectionDomain().getCodeSource().getLocation());
        String harnessSrc = String.valueOf(harness.getProtectionDomain().getCodeSource().getLocation());
        System.out.println("[launch] game classes from " + gameSrc);
        System.out.println("[launch] harness classes from " + harnessSrc);
        System.out.println("[launch] res overlay: " + (resDir == null ? "(none, jar only)" : resDir));
        rest.add(0, "--jar-path");
        rest.add(1, jarFile.toString());
        rest.add(2, "--res-path");
        rest.add(3, resDir == null ? "" : resDir.toString());

        Method run = harness.getMethod("run", String[].class, Map.class);
        int code;
        try {
            code = (Integer) run.invoke(null, rest.toArray(new String[0]), loader.used);
        } catch (InvocationTargetException ex) {
            ex.getCause().printStackTrace();
            code = 1;
        }
        System.exit(code);
    }
}
