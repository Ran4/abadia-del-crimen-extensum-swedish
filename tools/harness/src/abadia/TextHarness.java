package abadia;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import javax.imageio.ImageIO;

/**
 * Headless text-rendering harness for "La Abadia del Crimen Extensum".
 *
 * Lives in package abadia so it can call the game's package-private drawing code directly;
 * private members are reached by reflection. No Frame/Window is ever created and the game loop
 * is never started: only the static loaders (v.a(), j.a(), w.a(Abadia), y.a()) are called.
 *
 * NOTE: the game's classes are single letters (a, b, c, i, j, v, w, y, ...). In this file no
 * variable is allowed a one-letter name, because a local variable would obscure the class of
 * the same name.
 */
public final class TextHarness {

    // ------------------------------------------------------------------ reflection handles
    static Field jCs, jCt, jCu, jCv, jCw, jCo, jCz, jCm;
    static Method jStart, jPageBreak, jPageDraw, jGlyph;
    static Field wV, wF, wE, wH, wL, wM, wN, wO, wI, wT, wU;
    static Method wDraw, wSlots;
    static Field yI, yJ, yM, yF, yG, yP, yQ, yN, yO;
    static Field vH;

    static Field fld(Class<?> cls, String name) throws Exception {
        Field fd = cls.getDeclaredField(name);
        fd.setAccessible(true);
        return fd;
    }

    static Method mth(Class<?> cls, String name, Class<?>... params) throws Exception {
        Method md = cls.getDeclaredMethod(name, params);
        md.setAccessible(true);
        return md;
    }

    static void initReflection() throws Exception {
        Class<?> jc = abadia.j.class;
        jCs = fld(jc, "cs");
        jCt = fld(jc, "ct");
        jCu = fld(jc, "cu");
        jCv = fld(jc, "cv");
        jCw = fld(jc, "cw");
        jCo = fld(jc, "co");
        jCz = fld(jc, "cz");
        jCm = fld(jc, "cm");
        jStart = mth(jc, "c", int.class);        // private static void c(int): start message
        jPageBreak = mth(jc, "e");               // private static void e(): next 2-line page -> cv[]
        jPageDraw = mth(jc, "f");                // private static void f(): draw cv[] into cz
        jGlyph = mth(jc, "a", int.class, int.class, int.class, Graphics.class); // glyph switch
        Class<?> wc = abadia.w.class;
        wV = fld(wc, "v");
        wF = fld(wc, "f");
        wE = fld(wc, "e");
        wH = fld(wc, "h");
        wL = fld(wc, "l");
        wM = fld(wc, "m");
        wN = fld(wc, "n");
        wO = fld(wc, "o");
        wI = fld(wc, "i");
        wT = fld(wc, "t");
        wU = fld(wc, "u");
        wDraw = mth(wc, "a", int.class, int.class);
        wSlots = mth(wc, "c");
        Class<?> yc = abadia.y.class;
        yI = fld(yc, "i");
        yJ = fld(yc, "j");
        yM = fld(yc, "m");
        yF = fld(yc, "f");
        yG = fld(yc, "g");
        yP = fld(yc, "p");
        yQ = fld(yc, "q");
        yN = fld(yc, "n");
        yO = fld(yc, "o");
        vH = fld(abadia.v.class, "h");
    }

    static Object call(Method md, Object... args) throws Throwable {
        try {
            return md.invoke(null, args);
        } catch (InvocationTargetException ex) {
            throw ex.getCause();
        }
    }

    // ------------------------------------------------------------------ run state
    static String langCode;
    static int langIdx;
    static File outDir;
    static File rawDir;
    static boolean images = true;
    static boolean writeRaw = true;
    static int perSheet = 16;
    static String refLang;
    static final List<String> errors = new ArrayList<>();
    static final List<String> warnings = new ArrayList<>();
    static final List<String> missingGlyphs = new ArrayList<>();
    static final StringBuilder report = new StringBuilder();
    /** drawn[cp] = the game's glyph routine j.a(int,int,int,Graphics) puts at least one pixel. */
    static final boolean[] drawn = new boolean[65536];
    static boolean[] blankCell;
    static int fontGlyphs;

    static void err(String msg) {
        errors.add(msg);
    }

    static void warn(String msg) {
        warnings.add(msg);
    }

    static void rep(String msg) {
        report.append(msg).append('\n');
        System.out.println(msg);
    }

    // ------------------------------------------------------------------ entry point
    public static int run(String[] args, Map<String, String> usedResources) throws Throwable {
        String jarPath = "";
        String resPath = "";
        String out = null;
        List<String> msgFiles = new ArrayList<>();
        List<String> textFiles = new ArrayList<>();
        List<String> parchFiles = new ArrayList<>();
        boolean doBuiltin = true;
        boolean doParch = true;
        langCode = "es";
        for (int idx = 0; idx < args.length; idx++) {
            String arg = args[idx];
            switch (arg) {
                case "--jar-path": jarPath = args[++idx]; break;
                case "--res-path": resPath = args[++idx]; break;
                case "--lang": langCode = args[++idx]; break;
                case "--out": out = args[++idx]; break;
                case "--msgfile": msgFiles.add(args[++idx]); break;
                case "--textfile": textFiles.add(args[++idx]); break;
                case "--parchfile": parchFiles.add(args[++idx]); break;
                case "--only-custom": doBuiltin = false; doParch = false; break;
                case "--no-parchment": doParch = false; break;
                case "--no-images": images = false; writeRaw = false; break;
                case "--no-raw": writeRaw = false; break;
                case "--per-sheet": perSheet = Integer.parseInt(args[++idx]); break;
                case "--ref-lang": refLang = args[++idx]; break;
                default:
                    System.err.println("unknown argument: " + arg);
                    return 1;
            }
        }
        if (out == null) {
            System.err.println("--out DIR is required");
            return 1;
        }
        langIdx = -1;
        for (int idx = 0; idx < Abadia.u.length; idx++) {
            if (Abadia.u[idx].equalsIgnoreCase(langCode)) {
                langIdx = idx;
            }
        }
        if (langIdx < 0) {
            System.err.println("unknown language " + langCode + "; Abadia.u = " + Arrays.toString(Abadia.u));
            return 1;
        }
        outDir = new File(out);
        rawDir = new File(outDir, "raw");
        outDir.mkdirs();
        if (writeRaw) {
            rawDir.mkdirs();
        }
        rep("TextHarness  lang=" + langCode + " (Abadia.a=" + langIdx + ")  jar=" + jarPath
                + "  res=" + (resPath.isEmpty() ? "(jar)" : resPath));

        initReflection();
        initGame();
        buildGlyphTable();

        Json js = new Json();
        js.open('{');
        js.key("lang").str(langCode).key("langIndex").num(langIdx).key("jar").str(jarPath).key("res").str(resPath);
        js.key("fontGlyphs").num(fontGlyphs);

        if (doBuiltin) {
            renderGlyphSheet();
            String[] gArr = abadia.j.b;          // = bS[Abadia.a] = <langclass>.g
            js.key("messages").open('[');
            renderMessages("g", gArr, 1, js);
            js.close(']');
            js.key("endgame").open('[');
            renderEndGame(js);
            js.close(']');
            js.key("menu").open('[');
            renderMenu(js);
            js.close(']');
            js.key("hours").open('[');
            renderHours(js);
            js.close(']');
            if (refLang != null) {
                compareWithReference();
            }
        }
        int custom = 0;
        for (String file : msgFiles) {
            List<String> lines = readLines(file);
            String[] arr = new String[lines.size() + 1];
            arr[0] = "";
            for (int idx = 0; idx < lines.size(); idx++) {
                arr[idx + 1] = lines.get(idx);
            }
            js.key("customMessages" + (custom == 0 ? "" : String.valueOf(custom))).open('[');
            renderMessages("custom" + (custom == 0 ? "" : String.valueOf(custom)), arr, 1, js);
            js.close(']');
            custom++;
        }
        int ctext = 0;
        for (String file : textFiles) {
            js.key("customText" + (ctext == 0 ? "" : String.valueOf(ctext))).open('[');
            renderCustomText("text" + (ctext == 0 ? "" : String.valueOf(ctext)), readLines(file), js);
            js.close(']');
            ctext++;
        }
        if (doParch || !parchFiles.isEmpty()) {
            js.key("parchment").open('{');
            initParchment();
            if (doParch) {
                runParchment("intro", abadia.y.c, js);
                runParchment("ending", abadia.y.d, js);
            }
            int pn = 0;
            for (String file : parchFiles) {
                byte[] data = Files.readAllBytes(new File(file).toPath());
                runParchment("custom" + (pn == 0 ? "" : String.valueOf(pn)), data, js);
                pn++;
            }
            js.close('}');
        }

        js.key("resources").open('{');
        for (Map.Entry<String, String> ent : new TreeMap<>(usedResources).entrySet()) {
            js.key(ent.getKey()).str(ent.getValue());
        }
        js.close('}');
        js.key("errors").open('[');
        for (String msg : errors) {
            js.str(msg);
        }
        js.close(']');
        js.key("warnings").open('[');
        for (String msg : warnings) {
            js.str(msg);
        }
        js.close(']');
        js.close('}');
        Files.write(new File(outDir, "layout.json").toPath(), js.toString().getBytes(StandardCharsets.UTF_8));

        rep("");
        rep("resources used:");
        for (Map.Entry<String, String> ent : new TreeMap<>(usedResources).entrySet()) {
            rep("  " + ent.getKey() + " <- " + ent.getValue());
        }
        rep("");
        rep("WARNINGS (" + warnings.size() + "):");
        for (String msg : warnings) {
            rep("  " + msg);
        }
        rep("ERRORS (" + errors.size() + "), of which missing glyphs: " + missingGlyphs.size());
        for (String msg : errors) {
            rep("  " + msg);
        }
        int code = errors.isEmpty() ? 0 : 2;
        rep("RESULT: " + (code == 0 ? "OK" : "FAIL") + " (exit " + code + ")");
        Files.write(new File(outDir, "report.txt").toPath(), report.toString().getBytes(StandardCharsets.UTF_8));
        if (!missingGlyphs.isEmpty()) {
            System.err.println("MISSING GLYPHS:");
            for (String msg : missingGlyphs) {
                System.err.println("  " + msg);
            }
        }
        return code;
    }

    static List<String> readLines(String file) throws IOException {
        List<String> res = new ArrayList<>();
        for (String line : Files.readAllLines(new File(file).toPath(), StandardCharsets.UTF_8)) {
            if (line.startsWith("#")) {
                continue;
            }
            res.add(line);
        }
        return res;
    }

    // ------------------------------------------------------------------ game initialisation
    static void initGame() throws Throwable {
        Abadia.a = langIdx;
        // v.a(): marcador.png (per language), numRoman.png, fuente.png (v.c, v.b=v.c), black-tinted
        // copy of fuente.png (v.d, palette * Abadia.az = 0), hour bytes v.a = <langclass>.b
        abadia.v.a();
        // j.a(): caras.png -> cx, dialog.png -> cy, Abadia.ae, j.b = <lang>.g, j.a = <lang>.a
        abadia.j.a();
        // w.a(Abadia): pause-menu strings l=f, m=d, n=c, o=e, j=w.t[lang], k=w.u[lang]
        abadia.w.a((Abadia) null);
        abadia.w.b = abadia.i.b("pergamino2.png");   // as Abadia.a() does
        fontGlyphs = abadia.v.c.getWidth(null) / 8;
        BufferedImage font = toBuffered(abadia.v.c);
        blankCell = new boolean[fontGlyphs];
        for (int gi = 0; gi < fontGlyphs; gi++) {
            boolean any = false;
            for (int px = 0; px < 8; px++) {
                for (int py = 0; py < font.getHeight(); py++) {
                    if ((font.getRGB(gi * 8 + px, py) >>> 24) != 0) {
                        any = true;
                    }
                }
            }
            blankCell[gi] = !any;
        }
        rep("fuente.png: " + abadia.v.c.getWidth(null) + "x" + abadia.v.c.getHeight(null) + " = " + fontGlyphs
                + " glyphs (codes 45.." + (44 + fontGlyphs) + ")");
    }

    static BufferedImage toBuffered(Image img) {
        BufferedImage bi = new BufferedImage(img.getWidth(null), img.getHeight(null), BufferedImage.TYPE_INT_ARGB);
        Graphics gr = bi.getGraphics();
        gr.drawImage(img, 0, 0, null);
        gr.dispose();
        return bi;
    }

    static BufferedImage copy(BufferedImage src, int sx, int sy, int sw, int sh) {
        BufferedImage bi = new BufferedImage(sw, sh, BufferedImage.TYPE_INT_RGB);
        Graphics gr = bi.getGraphics();
        gr.drawImage(src, -sx, -sy, null);
        gr.dispose();
        return bi;
    }

    // ------------------------------------------------------------------ glyph coverage
    /** Empirical: draw every BMP code point through the game's private j.a(int,int,int,Graphics). */
    static void buildGlyphTable() throws Throwable {
        BufferedImage cell = new BufferedImage(24, 24, BufferedImage.TYPE_INT_ARGB);
        int[] blank = new int[24 * 24];
        int count = 0;
        StringBuilder nonAscii = new StringBuilder();
        for (int cp = 0; cp < 65536; cp++) {
            cell.setRGB(0, 0, 24, 24, blank, 0, 24);
            Graphics gr = cell.getGraphics();
            call(jGlyph, cp, 8, 8, gr);
            gr.dispose();
            boolean any = false;
            for (int px = 0; px < 24 && !any; px++) {
                for (int py = 0; py < 24; py++) {
                    if ((cell.getRGB(px, py) >>> 24) != 0) {
                        any = true;
                        break;
                    }
                }
            }
            drawn[cp] = any;
            if (any) {
                count++;
                if (cp > 126) {
                    nonAscii.append(String.format(" U+%04X(%c)", cp, (char) cp));
                }
            }
        }
        // Static rule read from the bytecode of j.a(int,int,int,Graphics): see harness.md.
        int mismatches = 0;
        for (int cp = 0; cp < 65536; cp++) {
            boolean predicted = staticHasInk(cp);
            if (predicted != drawn[cp]) {
                mismatches++;
                if (mismatches <= 20) {
                    warn(String.format("glyph rule: static prediction %s but game draws %s for U+%04X",
                            predicted, drawn[cp], cp));
                }
            }
        }
        rep("glyph table: " + count + " code points produce ink via j.a(int,...); static-rule mismatches: "
                + mismatches + (mismatches == 0 ? " (bytecode rule confirmed)" : " (EMPIRICAL TABLE WINS)"));
        rep("drawable code points > U+007E:" + nonAscii);
        StringBuilder ascii = new StringBuilder();
        for (int cp = 32; cp < 127; cp++) {
            ascii.append(drawn[cp] ? (char) cp : '.');
        }
        rep("ASCII 32..126 with ink ('.' = none): " + ascii);
        // coverage file
        try (PrintWriter pw = new PrintWriter(new File(outDir, "coverage.txt"), "UTF-8")) {
            pw.println("# code points for which abadia.j.a(int,int,int,Graphics) draws ink (empirical)");
            pw.println("# space (U+0020) draws nothing but is a valid blank; '_' and '%' are line breaks in j.a(String,...)");
            for (int cp = 0; cp < 65536; cp++) {
                if (drawn[cp]) {
                    pw.printf("U+%04X %c%n", cp, (char) cp);
                }
            }
        }
    }

    /** Glyph switch of j.a(int,int,int,Graphics) as read from the bytecode (pristine jar). */
    static int[] staticMap(int cp) {
        // returns {base, accentCode or 0}
        switch (cp) {
            case 33: return new int[]{93, 0};
            case 39: return new int[]{97, 0};
            case 44: return new int[]{60, 0};
            case 120: case 202: return new int[]{69, 105};
            case 161: return new int[]{92, 0};
            case 191: return new int[]{64, 0};
            case 192: return new int[]{65, 104};
            case 193: return new int[]{65, 96};
            case 194: return new int[]{65, 105};
            case 196: return new int[]{65, 61};
            case 199: return new int[]{106, 0};
            case 200: return new int[]{69, 104};
            case 201: return new int[]{69, 96};
            case 204: return new int[]{73, 104};
            case 205: return new int[]{73, 96};
            case 206: return new int[]{73, 105};
            case 209: return new int[]{94, 0};
            case 210: return new int[]{79, 104};
            case 211: return new int[]{79, 96};
            case 212: return new int[]{79, 105};
            case 214: return new int[]{79, 61};
            case 217: return new int[]{85, 104};
            case 218: return new int[]{85, 96};
            case 219: return new int[]{85, 105};
            case 220: return new int[]{85, 61};
            case 223: return new int[]{62, 0};
            case 260: return new int[]{65, 116};
            case 262: return new int[]{67, 96};
            case 280: return new int[]{69, 116};
            case 321: return new int[]{114, 0};
            case 323: return new int[]{78, 96};
            case 338: return new int[]{107, 0};
            case 346: return new int[]{83, 96};
            case 377: return new int[]{90, 96};
            case 379: return new int[]{90, 115};
            default: return new int[]{cp, 0};
        }
    }

    static boolean rawInk(int code) {
        return code >= 45 && code - 45 < fontGlyphs && !blankCell[code - 45];
    }

    static boolean staticHasInk(int cp) {
        int[] mp = staticMap(cp);
        if (mp[0] != 32 && mp[0] < 45) {
            return false;
        }
        return rawInk(mp[0]) || (mp[1] != 0 && rawInk(mp[1]));
    }

    /**
     * Validate a string drawn with j.a(String,int,int,Graphics).
     * context "msg": '*' is the message line-end marker (drawn as nothing) and is allowed.
     */
    static void checkChars(String where, String text, boolean message) {
        for (int pos = 0; pos < text.length(); pos++) {
            char ch = text.charAt(pos);
            if (ch == ' ' || ch == '_' || ch == '%') {
                continue;
            }
            if (message && ch == '*') {
                continue;
            }
            if (!drawn[ch]) {
                String msg = String.format("MISSING GLYPH %s pos %d: U+%04X '%s' in \"%s\"", where, pos, (int) ch,
                        ch < 32 ? "\\x" + Integer.toHexString(ch) : String.valueOf(ch), esc(text));
                missingGlyphs.add(msg);
                err(msg);
            }
        }
    }

    static String esc(String text) {
        StringBuilder sb = new StringBuilder();
        for (int pos = 0; pos < text.length(); pos++) {
            char ch = text.charAt(pos);
            if (ch < 32 || ch == 127) {
                sb.append(String.format("\\x%02x", (int) ch));
            } else {
                sb.append(ch);
            }
        }
        return sb.toString();
    }

    // ------------------------------------------------------------------ glyph sheet
    static void renderGlyphSheet() throws Throwable {
        if (!images) {
            return;
        }
        Sheet sheet = new Sheet("glyphs", 4);
        // the raw font, one cell per code 45..44+fontGlyphs, normal font (v.c) and menu font (v.d)
        for (int gi = 0; gi < fontGlyphs; gi += 16) {
            BufferedImage row = new BufferedImage(16 * 16, 12, BufferedImage.TYPE_INT_RGB);
            Graphics gr = row.getGraphics();
            gr.setColor(new Color(0x404040));
            gr.fillRect(0, 0, row.getWidth(), row.getHeight());
            StringBuilder lbl = new StringBuilder("raw ");
            for (int col = 0; col < 16 && gi + col < fontGlyphs; col++) {
                gr.setColor(Color.BLACK);
                gr.fillRect(col * 16, 2, 8, 8);
                gr.setClip(col * 16, 2, 8, 8);
                gr.drawImage(abadia.v.c, col * 16 - (gi + col) * 8, 2, null);
                gr.setClip(null);
            }
            gr.dispose();
            lbl.append(45 + gi).append("..").append(Math.min(44 + gi + 16, 44 + fontGlyphs));
            StringBuilder chars = new StringBuilder();
            for (int col = 0; col < 16 && gi + col < fontGlyphs; col++) {
                chars.append((char) (45 + gi + col)).append(' ');
            }
            sheet.add(lbl + "  " + chars, row);
        }
        // every non-ASCII drawable code point, through the game's switch (accents included)
        List<Integer> list = new ArrayList<>();
        for (int cp = 127; cp < 65536; cp++) {
            if (drawn[cp]) {
                list.add(cp);
            }
        }
        for (int start = 0; start < list.size(); start += 12) {
            BufferedImage row = new BufferedImage(12 * 20, 16, BufferedImage.TYPE_INT_RGB);
            Graphics gr = row.getGraphics();
            StringBuilder lbl = new StringBuilder();
            for (int col = 0; col < 12 && start + col < list.size(); col++) {
                int cp = list.get(start + col);
                Graphics g2 = row.getGraphics();
                call(jGlyph, cp, col * 20 + 4, 5, g2);
                g2.dispose();
                lbl.append(String.format("%c=%X ", (char) cp, cp));
            }
            gr.dispose();
            sheet.add(lbl.toString(), row);
        }
        sheet.write();
    }

    // ------------------------------------------------------------------ messages
    static BufferedImage captureMessageBox() throws Throwable {
        BufferedImage screen = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
        Graphics gr = screen.getGraphics();
        Abadia.al = gr;
        Abadia.ak = 0;                       // (ak & 16) == 0 -> blinking marker visible
        int savedCu = jCu.getInt(null);
        jCu.setInt(null, 0);                 // cu < 4 -> face frame cF = 0 (no random mouth)
        abadia.j.c();                        // game composition: cz at (0,146), face, marker
        jCu.setInt(null, savedCu);
        gr.dispose();
        return copy(screen, 0, 146, 320, 30);
    }

    static void renderMessages(String arrName, String[] arr, int first, Json js) throws Throwable {
        String[] savedB = abadia.j.b;
        abadia.j.b = arr;
        Sheet sheet = images ? new Sheet(arrName.equals("g") ? "messages" : arrName, 3) : null;
        int facesAvail = abadia.i.b("caras.png").getWidth(null) / 20;
        int pagesTotal = 0;
        for (int idx = first; idx < arr.length; idx++) {
            String raw = arr[idx];
            String where = arrName + "[" + idx + "]";
            js.open('{');
            js.key("array").str(arrName).key("index").num(idx).key("raw").str(raw);
            List<String> local = new ArrayList<>();
            // ---- pre-checks for things that would crash/hang the real game
            if (raw == null || raw.isEmpty()) {
                local.add("empty string (game: substring(3) -> StringIndexOutOfBoundsException)");
            } else if (raw.charAt(0) != '@') {
                warn(where + ": does not start with '@': j.c(int) does replace(\"@\",\" _ @\").substring(3), so the first 3 "
                        + "chars ('" + esc(raw.substring(0, Math.min(3, raw.length()))) + "') are dropped if this message is shown");
            }
            if (raw != null && raw.endsWith(" ")) {
                local.add("ends with a space: split(\" \") drops trailing empties, so j.b() calls e() after the last "
                        + "page and indexes cs[cs.length] (ArrayIndexOutOfBoundsException in the game loop)");
            }
            js.key("pages").open('[');
            if (raw != null) {
                try {
                    call(jStart, idx);
                    int pageNo = 0;
                    while (true) {
                        pageNo++;
                        int cw = jCw.getInt(null);
                        String[] cv = (String[]) jCv.get(null);
                        int speaker = jCo.getInt(null);
                        js.open('{');
                        js.key("speaker").num(speaker);
                        js.key("lines").open('[');
                        StringBuilder lblLines = new StringBuilder();
                        for (int ln = 0; ln < cw; ln++) {
                            js.str(cv[ln]);
                            checkChars(where + " page " + pageNo + " line " + (ln + 1), cv[ln], true);
                            String vis = cv[ln];
                            // visible length: f() draws all chars of the line incl. trailing space
                            int lastInk = vis.replaceAll("[ _]+$", "").length();
                            if (ln == 1 && lastInk >= 35) {
                                warn(where + " page " + pageNo + ": line 2 has 35 chars; char 35 (x=304..311) is "
                                        + "overlapped by the blinking continue-marker drawn at x=306,y=164");
                            }
                            if (vis.indexOf('%') >= 0) {
                                warn(where + " page " + pageNo + ": '%' in a message line is a line break (+14 px) in j.a(String)");
                            }
                            lblLines.append(ln == 0 ? "" : " / ").append(vis.trim());
                        }
                        js.close(']');
                        js.close('}');
                        if (speaker < 0 || speaker >= 15) {
                            local.add("speaker @" + speaker + " out of range 0..14 (j.ck[] sound table has 15 entries)");
                        } else if (speaker >= facesAvail) {
                            local.add("speaker @" + speaker + " has no face in caras.png (" + facesAvail + " faces)");
                        }
                        if (sheet != null || writeRaw) {
                            BufferedImage box = captureMessageBox();
                            String tag = String.format("%s[%d] %d", arrName, idx, pageNo);
                            if (sheet != null) {
                                sheet.add(tag + "  @" + speaker + "  " + lblLines, box);
                            }
                            if (writeRaw) {
                                ImageIO.write(box, "png", new File(rawDir,
                                        String.format("msg_%s%03d_p%d.png", arrName, idx, pageNo)));
                            }
                        }
                        pagesTotal++;
                        String[] cs = (String[]) jCs.get(null);
                        int ct = jCt.getInt(null);
                        if (ct >= cs.length) {
                            break;
                        }
                        call(jPageBreak);
                        if (jCt.getInt(null) == ct) {
                            local.add("no progress at word " + ct + " '" + cs[ct] + "' (" + cs[ct].length()
                                    + " chars > 35): the game would show empty pages forever");
                            break;
                        }
                        call(jPageDraw);
                        if (pageNo > 200) {
                            local.add("more than 200 pages?");
                            break;
                        }
                    }
                } catch (NumberFormatException ex) {
                    local.add("speaker marker is not '@<digits>': " + ex.getMessage()
                            + " (game: NumberFormatException in j.e())");
                } catch (Throwable ex) {
                    local.add("game code threw " + ex);
                }
            }
            js.close(']');
            js.key("errors").open('[');
            for (String msg : local) {
                js.str(msg);
                err(where + ": " + msg);
            }
            js.close(']');
            js.close('}');
        }
        abadia.j.b = savedB;
        if (sheet != null) {
            sheet.write();
        }
        rep(arrName + ": " + (arr.length - first) + " messages, " + pagesTotal + " pages");
    }

    // ------------------------------------------------------------------ reference-language checks
    static List<String> speakerMarkers(String raw) {
        List<String> res = new ArrayList<>();
        if (raw == null) {
            return res;
        }
        java.util.regex.Matcher mt = java.util.regex.Pattern.compile("@[0-9]*").matcher(raw);
        while (mt.find()) {
            res.add(mt.group());
        }
        return res;
    }

    /**
     * --ref-lang: the per-language arrays of the target language must have the same sizes as the
     * reference language's, and every message must carry the same sequence of '@N' speaker
     * markers (they select face, voice sound and are consumed by j.e()).
     */
    static void compareWithReference() throws Throwable {
        int refIdx = -1;
        for (int idx = 0; idx < Abadia.u.length; idx++) {
            if (Abadia.u[idx].equalsIgnoreCase(refLang)) {
                refIdx = idx;
            }
        }
        if (refIdx < 0) {
            err("--ref-lang " + refLang + " unknown");
            return;
        }
        String[][] gAll = (String[][]) fld(abadia.j.class, "bS").get(null);
        String[][] aAll = (String[][]) fld(abadia.j.class, "bT").get(null);
        String[][] fAll = (String[][]) fld(abadia.w.class, "p").get(null);
        String[][] dAll = (String[][]) fld(abadia.w.class, "q").get(null);
        String[][] cAll = (String[][]) fld(abadia.w.class, "r").get(null);
        String[][] eAll = (String[][]) fld(abadia.w.class, "s").get(null);
        byte[][] bAll = (byte[][]) fld(abadia.v.class, "g").get(null);
        String[] names = {"g", "a", "f", "d", "c", "e"};
        String[][][] arrs = {gAll, aAll, fAll, dAll, cAll, eAll};
        for (int ai = 0; ai < names.length; ai++) {
            String[] mine = arrs[ai][langIdx];
            String[] ref = arrs[ai][refIdx];
            if (mine.length != ref.length) {
                err(names[ai] + " has " + mine.length + " entries, reference " + refLang + " has " + ref.length);
            }
            for (int idx = 0; idx < Math.min(mine.length, ref.length); idx++) {
                if (mine[idx] == null || mine[idx].isEmpty()) {
                    if (ref[idx] != null && !ref[idx].isEmpty()) {
                        if (mine[idx] != null && names[ai].equals("f") && idx >= 3 && idx <= 7) {
                            // label + value rows (w.java: v[i].concat(value)): an empty label is
                            // safe, the value carries the whole row (Swedish f[5], GLOSSARY 6.3)
                            warn("f[" + idx + "] is an empty label (the row shows only its value)");
                        } else {
                            err(names[ai] + "[" + idx + "] is empty but " + refLang + " is not");
                        }
                    }
                }
            }
        }
        if (bAll[langIdx].length != bAll[refIdx].length) {
            err("hour bytes b: " + bAll[langIdx].length + " bytes, reference " + bAll[refIdx].length);
        }
        String[] mineG = gAll[langIdx];
        String[] refG = gAll[refIdx];
        int diffs = 0;
        for (int idx = 1; idx < Math.min(mineG.length, refG.length); idx++) {
            List<String> mm = speakerMarkers(mineG[idx]);
            List<String> rm = speakerMarkers(refG[idx]);
            if (!mm.equals(rm)) {
                diffs++;
                err("g[" + idx + "] speaker markers " + mm + " differ from " + refLang + " " + rm);
            }
            boolean mineAt = mineG[idx] != null && mineG[idx].startsWith("@");
            boolean refAt = refG[idx] != null && refG[idx].startsWith("@");
            if (mineAt != refAt) {
                err("g[" + idx + "] starts with '@': " + mineAt + ", in " + refLang + ": " + refAt);
            }
        }
        rep("reference check against " + refLang + ": " + diffs + " messages with different speaker markers");
    }

    // ------------------------------------------------------------------ end of game screen
    static void renderEndGame(Json js) throws Throwable {
        String[] arr = abadia.j.a;     // = bT[Abadia.a] = <langclass>.a
        String[] pcts = {"5", "95", "100"};
        Sheet sheet = images ? new Sheet("endgame", 3) : null;
        for (String pct : pcts) {
            BufferedImage screen = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
            Graphics gr = screen.getGraphics();
            Abadia.al = gr;
            Abadia.q();     // black 320x176, as E.a(Graphics) does before the strings
            // E.java (end of game, not won): exactly these four calls
            abadia.j.a(arr[0], -1, 32, Abadia.al);
            abadia.j.a(String.valueOf(pct).concat(arr[1]), -1, 48, Abadia.al);
            abadia.j.a(arr[2], -1, 64, Abadia.al);
            abadia.j.a(arr[3], -1, 128, Abadia.al);
            gr.dispose();
            BufferedImage crop = copy(screen, 0, 0, 320, 176);
            if (sheet != null) {
                sheet.add("end of game, pct=" + pct + "   a[0..3] centred at y=32,48,64,128", crop);
            }
            if (writeRaw) {
                ImageIO.write(crop, "png", new File(rawDir, "endgame_pct" + pct + ".png"));
            }
        }
        int[] ys = {32, 48, 64, 128};
        for (int idx = 0; idx < arr.length; idx++) {
            String text = idx == 1 ? "100" + arr[idx] : arr[idx];
            int len = text.length();
            int xx = 160 - (len << 2);
            js.open('{').key("array").str("a").key("index").num(idx).key("raw").str(arr[idx])
                    .key("x").num(xx).key("y").num(idx < 4 ? ys[idx] : -1).close('}');
            checkChars("a[" + idx + "]", arr[idx], false);
            if (xx < 0) {
                err("a[" + idx + "] too long: centred x=160-len*4=" + xx + " < 0 (" + len + " chars incl. pct; max 40)");
            }
            if (text.indexOf('_') >= 0 || text.indexOf('%') >= 0) {
                warn("a[" + idx + "] contains a line break; j.a centres on the whole length and restarts every line at the same x");
            }
        }
        if (sheet != null) {
            sheet.write();
        }
    }

    // ------------------------------------------------------------------ pause menu
    static void renderMenu(Json js) throws Throwable {
        String[] fArr = (String[]) wL.get(null);   // <lang>.f
        String[] dArr = (String[]) wM.get(null);   // <lang>.d
        String[] cArr = (String[]) wN.get(null);   // <lang>.c
        String[] eArr = (String[]) wO.get(null);   // <lang>.e
        String dayWord = ((String[]) wT.get(null))[langIdx];
        String emptyWord = ((String[]) wU.get(null))[langIdx];
        Sheet sheet = images ? new Sheet("menu", 3) : null;
        // three states so that every c/d/e string is shown once
        int[][] states = {
            // J(sfx), H(music?) , Abadia.c(control), fullscreen, w.i
            {0, 1, 1, 0, 1},
            {1, 0, 0, 1, 0},
            {2, 1, 1, 0, 1},
        };
        for (int si = 0; si < states.length; si++) {
            int[] st = states[si];
            String[] items = new String[fArr.length];
            for (int idx = 0; idx < fArr.length; idx++) {
                // replicates the suffix switch of w.a(int,int) (case 6 reads Abadia.s.a, the Frame)
                String suffix = "";
                switch (idx) {
                    case 3: suffix = eArr[st[0]]; break;
                    case 4: suffix = cArr[st[1]]; break;
                    case 5: suffix = dArr[st[2] == 1 ? 0 : 1]; break;
                    case 6: suffix = cArr[st[3]]; break;
                    case 7: suffix = cArr[st[4]]; break;
                    default: break;
                }
                items[idx] = fArr[idx].concat(suffix);
            }
            BufferedImage screen = drawMenu(items, si, 190, fArr.length * 10 + 20);
            String lbl = "pause menu state " + si + " (sel=" + si + ")";
            if (sheet != null) {
                sheet.add(lbl, copy(screen, 0, 0, 320, 176));
            }
            if (writeRaw) {
                ImageIO.write(copy(screen, 0, 0, 320, 176), "png", new File(rawDir, "menu_state" + si + ".png"));
            }
        }
        // save/load slot list: w.c() builds "DAY d" + 7 hour bytes, or the EMPTY word
        byte[][] slotSets = {
            {0, 0x10, 0x21, 0x32, 0x43, 0x54, 0x65},
            {0x76, 0x16, 0, 0, 0, 0, 0},
        };
        for (int si = 0; si < slotSets.length; si++) {
            wE.set(null, slotSets[si].clone());
            call(wSlots);
            String[] slots = ((String[]) wH.get(null)).clone();
            BufferedImage screen = drawMenu(slots, 1, 120, 100);
            if (sheet != null) {
                StringBuilder lbl = new StringBuilder("save/load slots set " + si + ":");
                for (String sl : slots) {
                    lbl.append(" [").append(sl).append(']');
                }
                sheet.add(lbl.toString(), copy(screen, 0, 0, 320, 176));
            }
            if (writeRaw) {
                ImageIO.write(copy(screen, 0, 0, 320, 176), "png", new File(rawDir, "slots_set" + si + ".png"));
            }
            for (int idx = 0; idx < slots.length; idx++) {
                checkChars("w.h slot " + idx + " (set " + si + ")", slots[idx], false);
                checkMenuWidth("w.h slot " + idx, slots[idx], 120);
            }
        }
        // json + checks for the raw arrays
        String[][] all = {fArr, cArr, dArr, eArr};
        String[] names = {"f", "c", "d", "e"};
        for (int ai = 0; ai < all.length; ai++) {
            for (int idx = 0; idx < all[ai].length; idx++) {
                js.open('{').key("array").str(names[ai]).key("index").num(idx).key("raw").str(all[ai][idx]).close('}');
                checkChars(names[ai] + "[" + idx + "]", all[ai][idx], false);
            }
        }
        for (int idx = 0; idx < fArr.length; idx++) {
            String longest = fArr[idx];
            String[] sufs = idx == 3 ? eArr : idx == 4 || idx == 6 || idx == 7 ? cArr : idx == 5 ? dArr : new String[]{""};
            for (String sf : sufs) {
                if ((fArr[idx] + sf).length() > longest.length()) {
                    longest = fArr[idx] + sf;
                }
            }
            checkMenuWidth("f[" + idx + "]+suffix", longest, 190);
        }
        js.open('{').key("array").str("w.t[lang] (DAY word, hard-coded in w.class)").key("index").num(langIdx)
                .key("raw").str(dayWord).close('}');
        js.open('{').key("array").str("w.u[lang] (EMPTY word, hard-coded in w.class)").key("index").num(langIdx)
                .key("raw").str(emptyWord).close('}');
        if (sheet != null) {
            sheet.write();
        }
    }

    static void checkMenuWidth(String where, String text, int bar) {
        int px = text.length() * 8;
        int xx = 160 - (text.length() << 2);
        // pergamino2.png is drawn centred: x = (320 - W) >> 1
        int bgW = abadia.w.b.getWidth(null);
        int bgX = (320 - bgW) >> 1;
        if (xx < bgX || xx + px > bgX + bgW) {
            err(where + " \"" + text + "\" is " + px + " px wide: x=" + xx + ".." + (xx + px)
                    + " leaves the menu parchment (x=" + bgX + ".." + (bgX + bgW) + ")");
        } else if (px > bar) {
            warn(where + " \"" + text + "\" is " + px + " px wide, wider than the " + bar + " px highlight bar");
        }
    }

    /** Calls the game's private w.a(int,int) with w.v = items (so the suffix switch is skipped). */
    static BufferedImage drawMenu(String[] items, int sel, int barW, int boxH) throws Throwable {
        BufferedImage screen = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
        Graphics gr = screen.getGraphics();
        Abadia.al = gr;
        Abadia.al.setClip(0, 0, 320, 208);
        Image savedFont = abadia.v.b;
        abadia.v.b = abadia.v.d;            // w.a(): menu text uses the black-tinted font
        wV.set(null, items);
        wF.setInt(null, sel);
        call(wDraw, barW, boxH);
        abadia.v.b = savedFont;
        gr.dispose();
        return screen;
    }

    // ------------------------------------------------------------------ HUD hour names
    static void renderHours(Json js) throws Throwable {
        byte[] hours = abadia.v.a;          // <langclass>.b, 7 x 7 bytes
        Sheet sheet = images ? new Sheet("hours", 3) : null;
        if (hours.length != 49) {
            err("hour byte array has " + hours.length + " bytes, expected 49");
        }
        for (int hr = 0; hr < 7; hr++) {
            BufferedImage screen = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
            Graphics gr = screen.getGraphics();
            Abadia.al = gr;
            // D.c(): l = 7*b ; v.e = 9 ; then v.c() runs once per frame until e == 0
            abadia.D.l = 7 * hr;
            abadia.v.e = 9;
            for (int step = 0; step < 9; step++) {
                abadia.v.c();
            }
            abadia.v.e();          // marcador.png at (0,176) + hour window h at (4,197)
            abadia.v.b(hr + 1);    // day numeral (numRoman.png) at (37,183), for context
            gr.dispose();
            BufferedImage hud = copy(screen, 0, 176, 320, 32);
            // empirical ink check per cell in the 56x8 window
            BufferedImage win = (BufferedImage) vH.get(null);
            StringBuilder sb = new StringBuilder();
            byte[] seven = Arrays.copyOfRange(hours, hr * 7, hr * 7 + 7);
            for (int cell = 0; cell < 7; cell++) {
                int code = seven[cell];
                sb.append(code >= 32 && code < 127 ? (char) code : '?');
                boolean ink = false;
                for (int px = 0; px < 8; px++) {
                    for (int py = 0; py < 8; py++) {
                        if ((win.getRGB(cell * 8 + px, py) & 0xFFFFFF) != 0x275947) {
                            ink = true;
                        }
                    }
                }
                if (code != 32 && !ink) {
                    String msg = String.format("MISSING GLYPH b hour %d cell %d: byte %d (0x%02x) draws nothing in the HUD "
                            + "(v.c() draws raw glyph (byte-45)*8, no switch)", hr, cell, code, code & 255);
                    missingGlyphs.add(msg);
                    err(msg);
                }
                if (code == 32 && ink) {
                    warn("hour " + hr + " cell " + cell + ": space but ink?");
                }
                // the save-slot list draws the same bytes through j.a(String) (switch applies)
                int[] mp = staticMap(code & 0xFFFF);
                if (mp[0] != code || mp[1] != 0) {
                    warn(String.format("hour %d cell %d: byte %d is remapped by the j.a glyph switch, so it looks "
                            + "different in the save/load slot list than in the HUD", hr, cell, code));
                }
            }
            js.open('{').key("index").num(hr).key("bytes").str(new String(seven, StandardCharsets.ISO_8859_1)).close('}');
            if (sheet != null) {
                sheet.add("b hour " + hr + " = \"" + sb + "\"  (HUD window 56x8 at 4,197)", hud);
            }
            if (writeRaw) {
                ImageIO.write(hud, "png", new File(rawDir, "hud_hour" + hr + ".png"));
            }
        }
        if (sheet != null) {
            sheet.write();
        }
    }

    // ------------------------------------------------------------------ custom centred strings
    static void renderCustomText(String name, List<String> lines, Json js) throws Throwable {
        Sheet sheet = images ? new Sheet(name, 3) : null;
        for (int idx = 0; idx < lines.size(); idx++) {
            String text = lines.get(idx);
            BufferedImage screen = new BufferedImage(320, 24, BufferedImage.TYPE_INT_RGB);
            Graphics gr = screen.getGraphics();
            abadia.j.a(text, -1, 8, gr);
            gr.dispose();
            checkChars(name + "[" + idx + "]", text, false);
            int xx = 160 - (text.length() << 2);
            if (xx < 0) {
                err(name + "[" + idx + "] wider than 320 px when centred (" + text.length() + " chars)");
            }
            js.open('{').key("index").num(idx).key("raw").str(text).key("x").num(xx).close('}');
            if (sheet != null) {
                sheet.add(name + "[" + idx + "] x=" + xx, screen);
            }
        }
        if (sheet != null) {
            sheet.write();
        }
    }

    // ------------------------------------------------------------------ parchment (abadia.y)
    static byte[] letras;
    /** true when abadia/y.class and res/letras are byte-identical to the pristine 2016 v1.3e jar. */
    static boolean pristineParchment;
    static final String PRISTINE_Y_CLASS = "8bb617b59d28b7af127335396e248852f237951f74883bbb153d8e1aeb1b0e83";
    static final String PRISTINE_LETRAS = "047ebed09a422ebf4ac8a50b4fd56067289fdc08b820b93f5b91d5de2e362b52";

    static String sha256(byte[] data) throws Exception {
        byte[] dig = java.security.MessageDigest.getInstance("SHA-256").digest(data);
        StringBuilder sb = new StringBuilder();
        for (byte bt : dig) {
            sb.append(String.format("%02x", bt & 255));
        }
        return sb.toString();
    }

    static byte[] readResource(String name) throws IOException {
        try (java.io.InputStream in = TextHarness.class.getClassLoader().getResourceAsStream(name)) {
            if (in == null) {
                return new byte[0];
            }
            java.io.ByteArrayOutputStream bo = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int nr;
            while ((nr = in.read(buf)) > 0) {
                bo.write(buf, 0, nr);
            }
            return bo.toByteArray();
        }
    }

    static void initParchment() throws Throwable {
        abadia.y.a();   // letras -> p, <lang>/pergamino1 -> c, <lang>/pergamino2 -> d, pergamino.png -> q
        letras = (byte[]) yP.get(null);
        String yHash = sha256(readResource("abadia/y.class"));
        String lHash = sha256(letras);
        pristineParchment = PRISTINE_Y_CLASS.equals(yHash) && PRISTINE_LETRAS.equals(lHash);
        rep("parchment code/data: y.class " + (PRISTINE_Y_CLASS.equals(yHash) ? "pristine" : "MODIFIED " + yHash)
                + ", letras " + (PRISTINE_LETRAS.equals(lHash) ? "pristine" : "MODIFIED " + lHash)
                + (pristineParchment ? "" : " -> static decoder findings are advisory (warnings); the real y.a() run decides"));
        Image parch = (Image) yQ.get(null);
        rep("parchment: letras " + letras.length + " bytes, pergamino.png " + parch.getWidth(null) + "x"
                + parch.getHeight(null) + ", intro " + (abadia.y.c == null ? "MISSING" : abadia.y.c.length + " bytes")
                + ", ending " + (abadia.y.d == null ? "MISSING" : abadia.y.d.length + " bytes"));
    }

    /** One decoded glyph or control from the static re-implementation of y.a() case 1. */
    static final class PEvent {
        int offset;
        int page;
        int line;
        int xStart;
        int xEnd;
        String display;
        String problem;
    }

    /** 2nd-byte table of y.a() for lead bytes C3/C4/C5 and the character each entry was made for. */
    static final Map<Integer, String> UTF8_SECOND = new LinkedHashMap<>();

    static {
        UTF8_SECOND.put(130, "ł");
        UTF8_SECOND.put(132, "ń");
        UTF8_SECOND.put(133, "ą");
        UTF8_SECOND.put(135, "ć");
        UTF8_SECOND.put(153, "ę");
        UTF8_SECOND.put(155, "ś");
        UTF8_SECOND.put(161, "á");
        UTF8_SECOND.put(169, "é");
        UTF8_SECOND.put(173, "í");
        UTF8_SECOND.put(177, "ñ");
        UTF8_SECOND.put(179, "ó");
        UTF8_SECOND.put(186, "ź");
        UTF8_SECOND.put(188, "ż");
    }

    static int le16(int idx) {
        return (letras[idx] & 255) + ((letras[idx + 1] & 255) << 8);
    }

    /**
     * Static decoder replicating y.a(Graphics,Graphics) case 1 (byte decoding, accent flags,
     * glyph lookup (f-44)*2 in letras, advance = low nibble of the 0xF? terminator), CR = new
     * line (+16 px, page break when y > 178), LF = page break, 0x1A = end.
     */
    /** Rightmost x (absolute screen x) of any ink pixel of the last decodeParchment() call. */
    static int inkRight;

    static List<PEvent> decodeParchment(byte[] text, List<String> lineTexts, List<Integer> lineWidths,
            List<Integer> linePages) {
        inkRight = 0;
        List<PEvent> events = new ArrayList<>();
        int pos = 0;
        int xx = 76;
        int yy = 18;
        int page = 1;
        int line = 1;
        StringBuilder cur = new StringBuilder();
        int maxX = 76;
        boolean ended = false;
        while (pos < text.length) {
            int fb = text[pos] & 255;
            if (fb == 10 || fb == 13 || fb == 26) {
                lineTexts.add(cur.toString());
                lineWidths.add(maxX - 76);
                linePages.add(page);
                cur.setLength(0);
                maxX = 76;
                xx = 76;
                if (fb == 26) {
                    ended = true;
                    break;
                }
                if (fb == 10) {
                    yy = 18;
                    page++;
                    line = 1;
                } else {
                    yy += 16;
                    line++;
                    if (yy > 178) {
                        yy = 18;
                        page++;
                        line = 1;
                    }
                }
                pos++;
                continue;
            }
            if (fb == 32) {
                xx += 8;
                cur.append(' ');
                pos++;
                continue;
            }
            PEvent ev = new PEvent();
            ev.offset = pos;
            ev.page = page;
            ev.line = line;
            ev.xStart = xx;
            int fc = fb;
            String accent = "";
            String srcBytes = String.format("%02x", fb);
            switch (fb) {
                case 39: case 146: case 180:
                    pos++;
                    fc = pos < text.length ? text[pos] & 255 : -1;
                    srcBytes += String.format(" %02x", fc);
                    accent = "'";
                    break;
                case 192: fc = 65; accent = "`"; break;
                case 195: case 196: case 197: {
                    pos++;
                    int sb = pos < text.length ? text[pos] & 255 : -1;
                    srcBytes += String.format(" %02x", sb);
                    // y.a() ignores which of C3/C4/C5 it saw and keys only on the 2nd byte
                    String meant = sb >= 0x80 && sb <= 0xBF
                            ? String.valueOf((char) (((fb & 0x1F) << 6) | (sb & 0x3F))) : null;
                    String drawnAs = UTF8_SECOND.get(sb);
                    if (meant == null) {
                        ev.problem = String.format("byte %02x is taken as a UTF-8 lead byte by y.a() (Latin-1 %c?) and "
                                + "swallows the next byte %02x", fb, (char) fb, sb);
                    } else if (drawnAs != null && !drawnAs.equals(meant)) {
                        ev.problem = String.format("UTF-8 %s (U+%04X) is drawn as '%s' (y.a() keys on the 2nd byte only)",
                                meant, (int) meant.charAt(0), drawnAs);
                    }
                    switch (sb) {
                        case 130: fc = 108; accent = "/"; break;
                        case 132: fc = 110; accent = "´"; break;
                        case 133: fc = 97; accent = "˛"; break;
                        case 135: fc = 99; accent = "´"; break;
                        case 153: fc = 101; accent = "˛"; break;
                        case 155: fc = 115; accent = "´"; break;
                        case 161: fc = 97; accent = "´"; break;
                        case 169: fc = 101; accent = "´"; break;
                        case 173: fc = 105; accent = "´"; break;
                        case 177: fc = 47; break;
                        case 179: fc = 111; accent = "´"; break;
                        case 186: fc = 122; accent = "´"; break;
                        case 188: fc = 122; accent = "˙"; break;
                        default: fc = sb; break;
                    }
                    break;
                }
                case 224: fc = 97; accent = "`"; break;
                case 225: fc = 97; accent = "´"; break;
                case 231: fc = 99; accent = "¸"; break;
                case 232: fc = 101; accent = "`"; break;
                case 233: fc = 101; accent = "´"; break;
                case 236: fc = 105; accent = "`"; break;
                case 237: fc = 105; accent = "´"; break;
                case 241: fc = 47; break;
                case 242: fc = 111; accent = "`"; break;
                case 243: fc = 111; accent = "´"; break;
                case 249: fc = 117; accent = "`"; break;
                case 250: fc = 117; accent = "´"; break;
                default: break;
            }
            switch (fc) {
                case 226: fc = 97; accent = "^"; break;
                case 234: fc = 101; accent = "^"; break;
                case 238: fc = 105; accent = "^"; break;
                case 244: fc = 111; accent = "^"; break;
                case 251: fc = 117; accent = "^"; break;
                default: break;
            }
            ev.display = (fc == 47 ? "ñ" : fc >= 32 && fc < 127 ? String.valueOf((char) fc) : "?") + accent;
            int tbl = (fc - 44) << 1;
            int adv = 0;
            String leadProblem = ev.problem;
            ev.problem = null;
            if (fc < 44) {
                ev.problem = "byte(s) " + srcBytes + " decode to " + fc + " < 44: (f-44)*2 is negative -> "
                        + "ArrayIndexOutOfBoundsException in y.a() case 1 (uncaught; parchment never advances)";
            } else if (fc > 124 && pristineParchment) {
                ev.problem = "byte(s) " + srcBytes + " decode to " + fc + " > 124: past the 81-entry glyph table of "
                        + "letras (entries for 44..124), offset read from glyph data = garbage/negative";
            } else {
                int off = tbl + 1 < letras.length ? le16(tbl) - 42711 : -1;
                if (off < 0 || off >= letras.length) {
                    ev.problem = "byte(s) " + srcBytes + " decode to '" + (char) fc + "' (" + fc
                            + ") which has NO glyph in letras (table entry 0): the game prints 'Caracter: " + fc
                            + "' every frame and the parchment hangs";
                } else {
                    int gp = off;
                    while (gp < letras.length && (letras[gp] & 0xF0) != 0xF0) {
                        inkRight = Math.max(inkRight, xx + (letras[gp] & 15));
                        gp++;
                    }
                    adv = gp < letras.length ? letras[gp] & 15 : 0;
                }
            }
            if (leadProblem != null) {
                ev.problem = leadProblem + (ev.problem == null ? "" : "; " + ev.problem);
            }
            xx += adv;
            ev.xEnd = xx;
            maxX = Math.max(maxX, xx);
            cur.append(ev.display);
            events.add(ev);
            pos++;
        }
        if (!ended) {
            lineTexts.add(cur.toString());
            lineWidths.add(maxX - 76);
            linePages.add(page);
            PEvent ev = new PEvent();
            ev.offset = text.length;
            ev.display = "";
            ev.problem = "no 0x1A terminator: y.a() would read past the end of the array";
            events.add(ev);
        }
        return events;
    }

    static void runParchment(String name, byte[] text, Json js) throws Throwable {
        js.key(name).open('{');
        if (text == null) {
            err("parchment " + name + ": text resource missing");
            js.close('}');
            return;
        }
        List<String> lineTexts = new ArrayList<>();
        List<Integer> lineWidths = new ArrayList<>();
        List<Integer> linePages = new ArrayList<>();
        List<PEvent> events = decodeParchment(text, lineTexts, lineWidths, linePages);
        int staticPages = linePages.isEmpty() ? 0 : linePages.get(linePages.size() - 1);
        for (PEvent ev : events) {
            if (ev.problem != null) {
                String msg = "MISSING GLYPH parchment " + name + " offset " + ev.offset + " (page " + ev.page + " line "
                        + ev.line + "): " + ev.problem;
                if (pristineParchment) {
                    missingGlyphs.add(msg);
                    err(msg);
                } else {
                    warn("(static decoder, advisory) " + msg);
                }
            }
        }
        // ---- drive the real state machine y.a(Graphics,Graphics) offscreen
        BufferedImage back = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);   // Abadia.ac
        Abadia.ac = back;
        Abadia.ad = back.getGraphics();
        BufferedImage screen = new BufferedImage(320, 208, BufferedImage.TYPE_INT_RGB);
        Graphics scr = screen.getGraphics();
        Abadia.al = scr;
        abadia.y.b = text;
        abadia.y.a = 0;
        abadia.y.e = -1;       // y.a() calls Abadia.aj.a(e) (music) when e >= 0
        List<BufferedImage> pages = new ArrayList<>();
        long steps = 0;
        String failure = null;
        while (abadia.y.a != -1) {
            int before = abadia.y.a;
            int gBefore = yG.getInt(null);
            int mBefore = yM.getInt(null);
            try {
                abadia.y.a(Abadia.ad, scr);
            } catch (Throwable ex) {
                failure = "y.a() threw " + ex + " at text offset " + mBefore + " (byte 0x"
                        + Integer.toHexString(text[Math.min(mBefore, text.length - 1)] & 255) + ")";
                break;
            }
            steps++;
            int after = abadia.y.a;
            if (before == 2 && after == 2 && yG.getInt(null) == gBefore) {
                failure = "stuck drawing char " + yF.getInt(null) + " decoded from the byte(s) ending at offset " + (mBefore - 1)
                        + " (no glyph in letras; the game would hang here)";
                break;
            }
            if ((after == 3 && before != 3) || after == -1) {
                pages.add(copy(back, 0, 0, 320, 208));
            }
            if (steps > 20_000_000L) {
                failure = "more than 20M steps";
                break;
            }
        }
        if (failure != null) {
            err("parchment " + name + ": " + failure);
            pages.add(copy(back, 0, 0, 320, 208));   // state at the failure
        }
        if (failure == null && pages.size() != staticPages) {
            warn("parchment " + name + ": static decoder predicts " + staticPages + " pages, game produced " + pages.size());
        }
        int maxW = 0;
        for (int width : lineWidths) {
            maxW = Math.max(maxW, width);
        }
        rep("parchment " + name + ": " + pages.size() + " pages, " + lineTexts.size() + " lines, widest line "
                + maxW + " px (text starts x=76), rightmost ink pixel x=" + inkRight + " (parchment image x=65..254), " + steps + " y.a() steps" + (failure != null ? ", FAILED: " + failure : ""));
        js.key("pages").num(pages.size()).key("steps").num((int) Math.min(steps, Integer.MAX_VALUE));
        js.key("maxLineWidthPx").num(maxW);
        js.key("rightmostInkX").num(inkRight);
        js.key("lines").open('[');
        for (int idx = 0; idx < lineTexts.size(); idx++) {
            js.open('{').key("page").num(linePages.get(idx)).key("widthPx").num(lineWidths.get(idx))
                    .key("text").str(lineTexts.get(idx)).close('}');
        }
        js.close(']');
        js.close('}');
        if (images) {
            Sheet sheet = new Sheet("parchment_" + name, 3);
            for (int idx = 0; idx < pages.size(); idx++) {
                sheet.add("parchment " + name + " page " + (idx + 1) + "/" + pages.size(), pages.get(idx));
            }
            sheet.perSheet = 6;
            sheet.columns = 2;
            sheet.write();
        }
        if (writeRaw) {
            for (int idx = 0; idx < pages.size(); idx++) {
                ImageIO.write(pages.get(idx), "png", new File(rawDir, String.format("parch_%s_p%02d.png", name, idx + 1)));
            }
        }
    }

    // ------------------------------------------------------------------ contact sheets
    static final class Sheet {
        final String name;
        final int scale;
        int perSheet = TextHarness.perSheet;
        int columns = 1;
        final List<String> labels = new ArrayList<>();
        final List<BufferedImage> imgs = new ArrayList<>();

        Sheet(String name, int scale) {
            this.name = name;
            this.scale = scale;
        }

        void add(String label, BufferedImage img) {
            labels.add(label);
            imgs.add(img);
        }

        void write() throws IOException {
            if (imgs.isEmpty()) {
                return;
            }
            int sheets = (imgs.size() + perSheet - 1) / perSheet;
            Font font = new Font(Font.MONOSPACED, Font.PLAIN, 14);
            for (int sh = 0; sh < sheets; sh++) {
                int from = sh * perSheet;
                int to = Math.min(imgs.size(), from + perSheet);
                int cellW = 0;
                int cellH = 0;
                for (int idx = from; idx < to; idx++) {
                    cellW = Math.max(cellW, imgs.get(idx).getWidth() * scale);
                    cellH = Math.max(cellH, imgs.get(idx).getHeight() * scale);
                }
                int labelH = 20;
                int pad = 8;
                int rows = (to - from + columns - 1) / columns;
                int width = columns * (cellW + pad) + pad;
                int height = rows * (cellH + labelH + pad) + pad;
                BufferedImage out = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
                Graphics2D gr = out.createGraphics();
                gr.setColor(new Color(0x30, 0x30, 0x38));
                gr.fillRect(0, 0, width, height);
                gr.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);
                gr.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
                gr.setFont(font);
                for (int idx = from; idx < to; idx++) {
                    int slot = idx - from;
                    int cx = pad + (slot % columns) * (cellW + pad);
                    int cy = pad + (slot / columns) * (cellH + labelH + pad);
                    gr.setColor(new Color(0xFF, 0xE0, 0x80));
                    String lbl = labels.get(idx);
                    int maxChars = Math.max(10, cellW / 8 - 1);
                    if (lbl.length() > maxChars) {
                        lbl = lbl.substring(0, maxChars - 1) + "…";
                    }
                    gr.drawString(lbl, cx, cy + 15);
                    BufferedImage img = imgs.get(idx);
                    gr.drawImage(img, cx, cy + labelH, img.getWidth() * scale, img.getHeight() * scale, null);
                }
                gr.dispose();
                String file = sheets == 1 ? name + ".png" : String.format("%s_%02d.png", name, sh + 1);
                ImageIO.write(out, "png", new File(outDir, file));
            }
        }
    }

    // ------------------------------------------------------------------ minimal JSON writer
    static final class Json {
        final StringBuilder sb = new StringBuilder();
        final List<Boolean> first = new ArrayList<>();
        boolean afterKey;

        void sep() {
            if (afterKey) {
                afterKey = false;
                return;
            }
            if (!first.isEmpty()) {
                int top = first.size() - 1;
                if (!first.get(top)) {
                    sb.append(',');
                }
                first.set(top, false);
                sb.append('\n');
            }
        }

        Json open(char ch) {
            sep();
            sb.append(ch);
            first.add(true);
            return this;
        }

        Json close(char ch) {
            first.remove(first.size() - 1);
            sb.append(ch);
            return this;
        }

        Json key(String key) {
            sep();
            quote(key);
            sb.append(':');
            afterKey = true;
            return this;
        }

        Json str(String val) {
            sep();
            if (val == null) {
                sb.append("null");
            } else {
                quote(val);
            }
            return this;
        }

        Json num(int val) {
            sep();
            sb.append(val);
            return this;
        }

        void quote(String val) {
            sb.append('"');
            for (int pos = 0; pos < val.length(); pos++) {
                char ch = val.charAt(pos);
                switch (ch) {
                    case '"': sb.append("\\\""); break;
                    case '\\': sb.append("\\\\"); break;
                    case '\n': sb.append("\\n"); break;
                    case '\r': sb.append("\\r"); break;
                    case '\t': sb.append("\\t"); break;
                    default:
                        if (ch < 32 || ch > 126) {
                            sb.append(String.format("\\u%04x", (int) ch));
                        } else {
                            sb.append(ch);
                        }
                }
            }
            sb.append('"');
        }

        @Override
        public String toString() {
            return sb.toString() + "\n";
        }
    }

    private TextHarness() {
    }
}
