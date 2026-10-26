import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Paths;
import javax.imageio.ImageIO;

/**
 * Drives the REAL parchment writer abadia.y.a(Graphics,Graphics) headless, one call per game tick,
 * into BufferedImages (no window, no sound: abadia.c.b.a() is never called so sound flag G stays false).
 *
 * usage: java -Djava.awt.headless=true -cp <jar-dir-or-jar>:classes PergHarness LANGIDX N OUTDIR [TEXTFILE]
 *   LANGIDX: 0=es 1=en 2=it 3=fr 4=de 5=pl   N: 1 (intro, y.c) or 2 (ending, y.d)
 *   TEXTFILE: optional replacement text bytes (to test a candidate translation)
 * Writes OUTDIR/page<k>.png = Abadia.ac at the moment the page is complete (state 1->3 transition or end),
 * and prints per-page statistics (ticks, summed Abadia.e delay in ms).
 */
public class PergHarness {
    static Field f(Class<?> c, String n) throws Exception {
        Field x = c.getDeclaredField(n);
        x.setAccessible(true);
        return x;
    }

    public static void main(String[] args) throws Exception {
        int lang = Integer.parseInt(args[0]);
        int which = Integer.parseInt(args[1]);
        File out = new File(args[2]);
        out.mkdirs();
        Class<?> A = Class.forName("abadia.Abadia");
        Class<?> Y = Class.forName("abadia.y");
        f(A, "a").setInt(null, lang);
        Method load = Y.getDeclaredMethod("a");
        load.setAccessible(true);
        load.invoke(null);
        BufferedImage ac = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
        Graphics ad = ac.getGraphics();
        f(A, "ac").set(null, ac);
        f(A, "ad").set(null, ad);
        BufferedImage scr = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
        Graphics al = scr.getGraphics();
        f(A, "al").set(null, al);
        byte[] text = (byte[]) f(Y, which == 1 ? "c" : "d").get(null);
        if (args.length > 3) text = Files.readAllBytes(Paths.get(args[3]));
        f(Y, "b").set(null, text);
        f(Y, "a").setInt(null, 0);
        f(Y, "e").setInt(null, -1);
        Field ya = f(Y, "a"), ym = f(Y, "m"), Ae = f(A, "e"), yi = f(Y, "i"), yj = f(Y, "j");
        Method draw = Y.getDeclaredMethod("a", Graphics.class, Graphics.class);
        draw.setAccessible(true);
        int page = 1, prev = 0;
        long ticks = 0, pageTicks = 0, ms = 0, pageMs = 0, flipMs = 0, maxI = 0;
        long lastProgressTick = 0;
        int lastM = -1;
        while (true) {
            int st = ya.getInt(null);
            if (st == -1 || (st == 3 && prev != 3)) {
                ImageIO.write(ac, "png", new File(out, "page" + page + ".png"));
                System.out.printf("page %d: ticks=%d writing_ms(sum of Abadia.e)=%d%n", page, pageTicks, pageMs);
                if (st == -1) break;
                page++;
                pageTicks = 0;
                pageMs = 0;
            }
            try {
                draw.invoke(null, ad, al);
            } catch (InvocationTargetException e) {
                System.out.println("UNCAUGHT in y.a at state " + st + " m=" + ym.getInt(null) + ": " + e.getCause());
                ImageIO.write(ac, "png", new File(out, "page" + page + "_crash.png"));
                return;
            }
            int e = Ae.getInt(null);
            ticks++;
            ms += e;
            if (st == 3 || st == 4) flipMs += e; else { pageTicks++; pageMs += e; }
            maxI = Math.max(maxI, yi.getInt(null));
            int m = ym.getInt(null);
            if (m != lastM) { lastM = m; lastProgressTick = ticks; }
            if (ticks - lastProgressTick > 20000) {
                System.out.println("HANG: no text progress for 20000 ticks at m=" + m + " state=" + st);
                ImageIO.write(ac, "png", new File(out, "page" + page + "_hang.png"));
                return;
            }
            prev = st;
        }
        System.out.printf("END: Abadia.an=%s total_ticks=%d total_ms=%d (incl. page flips %d ms) max_pen_x=%d%n",
                f(A, "an").getBoolean(null), ticks, ms, flipMs, maxI);
    }
}
