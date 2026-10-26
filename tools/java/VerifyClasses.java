import java.io.*;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import org.objectweb.asm.*;
import org.objectweb.asm.util.CheckClassAdapter;

/**
 * Swedish build: verify patched/generated game classes (FORMAT §3.4 verification protocol).
 *
 * usage: java -Xverify:all -XX:-FailOverToOldVerifier -Djava.awt.headless=true \
 *            -cp asm-9.7.1.jar:asm-tree-9.7.1.jar:asm-analysis-9.7.1.jar:asm-util-9.7.1.jar:DIR \
 *            VerifyClasses --jar GAME.jar [--classes DIR] [--init abadia/k,abadia/w] [--dump OUT] CLASS...
 *
 * CLASS = internal name (abadia/j). The bytes come from --classes DIR when present there, else from
 * the jar. For each class:
 *   1. ClassReader.accept(new CheckClassAdapter(new ClassWriter(0), true), 0)   (structure + maxs)
 *   2. CheckClassAdapter.verify(reader, loader, false, pw)                       (ASM data flow)
 *   3. load it through a URLClassLoader over [--classes DIR,] GAME.jar whose parent is the platform
 *      loader, WITHOUT initialising it, and force linking (= JVM bytecode verification, which
 *      -Xverify:all applies to every class) with getDeclaredMethods/Fields/Constructors.
 * Then, for each --init class (only data-only static initialisers: k, w), initialise it and dump
 * every static String[] / byte[] field to --dump as  CLASS.FIELD[i]<TAB>VALUE  (escaped; bytes as
 * unsigned ints) for the caller to compare. Game classes that open windows (E, Abadia, F) must
 * never be passed to --init. Exit 0 = "VERIFY OK", 3 = a problem (printed).
 */
public class VerifyClasses {

    public static void main(String[] args) throws Exception {
        if (!"true".equals(System.getProperty("java.awt.headless"))) {
            System.err.println("refusing to run: pass -Djava.awt.headless=true");
            System.exit(1);
        }
        String jar = null, classesDir = null, dump = null;
        List<String> init = new ArrayList<>();
        List<String> classes = new ArrayList<>();
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--jar": jar = args[++i]; break;
                case "--classes": classesDir = args[++i]; break;
                case "--dump": dump = args[++i]; break;
                case "--init": init.addAll(Arrays.asList(args[++i].split(","))); break;
                default: classes.add(args[i]);
            }
        }
        if (jar == null || classes.isEmpty()) {
            System.err.println("usage: VerifyClasses --jar GAME.jar [--classes DIR] [--init a/b,c/d] [--dump OUT] CLASS...");
            System.exit(1);
        }
        for (String forbidden : new String[]{"abadia/E", "abadia/Abadia", "abadia/F"})
            if (init.contains(forbidden)) throw new IllegalArgumentException("never initialise " + forbidden);
        String jv = System.getProperty("java.version");
        List<URL> urls = new ArrayList<>();
        if (classesDir != null) urls.add(new File(classesDir).toURI().toURL());
        urls.add(new File(jar).toURI().toURL());
        URLClassLoader loader = new URLClassLoader(urls.toArray(new URL[0]), ClassLoader.getSystemClassLoader().getParent());
        List<String> problems = new ArrayList<>();
        try (ZipFile zf = new ZipFile(jar)) {
            for (String cls : classes) {
                byte[] b = null;
                if (classesDir != null) {
                    File f = new File(classesDir, cls + ".class");
                    if (f.isFile()) b = Files.readAllBytes(f.toPath());
                }
                if (b == null) {
                    ZipEntry ze = zf.getEntry(cls + ".class");
                    if (ze == null) { problems.add(cls + ": not found"); continue; }
                    try (InputStream in = zf.getInputStream(ze)) {
                        ByteArrayOutputStream bo = new ByteArrayOutputStream();
                        byte[] buf = new byte[8192];
                        int n;
                        while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                        b = bo.toByteArray();
                    }
                }
                ClassReader cr = new ClassReader(b);
                try {
                    cr.accept(new CheckClassAdapter(new ClassWriter(0), true), 0);
                } catch (Throwable t) {
                    problems.add(cls + ": CheckClassAdapter: " + t);
                }
                StringWriter sw = new StringWriter();
                PrintWriter pw = new PrintWriter(sw);
                try {
                    CheckClassAdapter.verify(new ClassReader(b), loader, false, pw);
                } catch (Throwable t) {
                    pw.println("exception " + t);
                }
                pw.flush();
                if (!sw.toString().trim().isEmpty()) problems.add(cls + ": CheckClassAdapter.verify:\n" + sw);
                try {
                    Class<?> c = Class.forName(cls.replace('/', '.'), false, loader);
                    if (c.getClassLoader() != loader) problems.add(cls + ": loaded by the wrong loader " + c.getClassLoader());
                    c.getDeclaredMethods();     // HotSpot links (verifies) the class here
                    c.getDeclaredFields();
                    c.getDeclaredConstructors();
                    System.out.println("LINK OK " + cls + " (java " + jv + ", " + b.length + " bytes, major " + cr.readShort(6) + ")");
                } catch (Throwable t) {
                    problems.add(cls + ": load/link: " + t);
                }
            }
        }
        StringBuilder out = new StringBuilder();
        for (String cls : init) {
            try {
                Class<?> c = Class.forName(cls.replace('/', '.'), true, loader);
                for (Field f : c.getDeclaredFields()) {
                    if (!Modifier.isStatic(f.getModifiers())) continue;
                    f.setAccessible(true);
                    Object v = f.get(null);
                    String key = cls + "." + f.getName();
                    if (v instanceof String[]) {
                        String[] s = (String[]) v;
                        out.append(key).append(".length\t").append(s.length).append('\n');
                        for (int i = 0; i < s.length; i++)
                            out.append(key).append('[').append(i).append("]\t").append(s[i] == null ? "<null>" : PatchStrings.escape(s[i])).append('\n');
                    } else if (v instanceof byte[]) {
                        byte[] s = (byte[]) v;
                        out.append(key).append(".length\t").append(s.length).append('\n');
                        for (int i = 0; i < s.length; i++)
                            out.append(key).append('[').append(i).append("]\t").append(s[i] & 255).append('\n');
                    }
                }
                System.out.println("INIT OK " + cls);
            } catch (Throwable t) {
                problems.add(cls + ": init: " + t);
            }
        }
        if (dump != null) Files.write(Paths.get(dump), out.toString().getBytes(StandardCharsets.UTF_8));
        if (!problems.isEmpty()) {
            for (String p : problems) System.out.println("PROBLEM " + p);
            System.out.println("VERIFY FAILED (java " + jv + ")");
            System.exit(3);
        }
        System.out.println("VERIFY OK (java " + jv + ", " + classes.size() + " classes)");
    }
}
