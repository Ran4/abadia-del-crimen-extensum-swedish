import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

/**
 * Swedish build: replace per-language string constants that live in a class's static initialiser,
 * e.g. w.t[4] "DÍA " -> "DAG ", w.u[4] "VACÍO" -> "TOM", E.h[4] (window title).
 * Port of work/phaseA/refute_deslot_1/scripts/PatchTW.java (FORMAT §1.10, DECISIONS D6).
 *
 * usage: java -cp asm-9.7.1.jar:asm-tree-9.7.1.jar:. PatchStrings <in.class> <out.class> <spec.tsv>
 *
 * spec.tsv (UTF-8): one replacement per line, "INDEX<TAB>OLD<TAB>NEW". OLD/NEW use backslash
 * escapes (\\ \t \n \r \\uXXXX) so leading/trailing spaces and non-ASCII survive any locale.
 *
 * For each line: in <clinit>, find every LDC whose String constant equals OLD and whose previous
 * real instruction pushes INDEX (ICONST_n / BIPUSH / SIPUSH); there must be exactly one such
 * site. Its constant becomes NEW. A new constant is appended to the pool (ASM switches to ldc_w
 * when the index needs it); existing pool entries are never edited, because es (index 0) shares
 * "DÍA " and "VACÍO" with index 4. ClassWriter(reader, 0) keeps the original constant pool, and
 * every method except <clinit> is copied verbatim. w.<clinit> and E.<clinit> have no branches,
 * so no frames are involved.
 */
public class PatchStrings {

    static String unescape(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c != '\\') {
                sb.append(c);
                continue;
            }
            char n = s.charAt(++i);
            switch (n) {
                case '\\': sb.append('\\'); break;
                case 't': sb.append('\t'); break;
                case 'n': sb.append('\n'); break;
                case 'r': sb.append('\r'); break;
                case 'u': sb.append((char) Integer.parseInt(s.substring(i + 1, i + 5), 16)); i += 4; break;
                default: throw new IllegalArgumentException("bad escape \\" + n + " in " + s);
            }
        }
        return sb.toString();
    }

    static String escape(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\') sb.append("\\\\");
            else if (c == '\t') sb.append("\\t");
            else if (c == '\n') sb.append("\\n");
            else if (c == '\r') sb.append("\\r");
            else if (c < 0x20 || c > 0x7e) sb.append(String.format("\\u%04x", (int) c));
            else sb.append(c);
        }
        return sb.toString();
    }

    /** The int pushed by an ICONST_n/BIPUSH/SIPUSH instruction, or null. */
    static Integer pushedInt(AbstractInsnNode n) {
        if (n == null) return null;
        int op = n.getOpcode();
        if (op >= Opcodes.ICONST_M1 && op <= Opcodes.ICONST_5) return op - Opcodes.ICONST_0;
        if (op == Opcodes.BIPUSH || op == Opcodes.SIPUSH) return ((IntInsnNode) n).operand;
        return null;
    }

    static AbstractInsnNode prevReal(AbstractInsnNode n) {
        AbstractInsnNode p = n.getPrevious();
        while (p != null && p.getOpcode() < 0) p = p.getPrevious();
        return p;
    }

    public static void main(String[] a) throws Exception {
        if (a.length != 3) {
            System.err.println("usage: PatchStrings <in.class> <out.class> <spec.tsv>");
            System.exit(1);
        }
        byte[] in = Files.readAllBytes(Paths.get(a[0]));
        final List<int[]> idxs = new ArrayList<>();
        final List<String[]> pairs = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(a[2]), StandardCharsets.UTF_8)) {
            if (line.isEmpty()) continue;
            String[] f = line.split("\t", -1);
            if (f.length != 3) throw new IllegalArgumentException("spec line needs 3 tab-separated fields: " + line);
            idxs.add(new int[]{Integer.parseInt(f[0])});
            pairs.add(new String[]{unescape(f[1]), unescape(f[2])});
        }
        if (pairs.isEmpty()) throw new IllegalArgumentException("empty spec");

        ClassReader cr = new ClassReader(in);
        if (cr.readShort(6) != 51) throw new IllegalStateException("expected class major version 51");
        ClassWriter cw = new ClassWriter(cr, 0);   // keeps the original constant pool: existing indices stay
        final int[] clinits = {0};
        final int[] hits = new int[pairs.size()];
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int acc, String name, String desc, String sig, String[] exc) {
                final MethodVisitor next = super.visitMethod(acc, name, desc, sig, exc);
                if (!name.equals("<clinit>")) return next;   // verbatim copy
                clinits[0]++;
                return new MethodNode(Opcodes.ASM9, acc, name, desc, sig, exc) {
                    @Override
                    public void visitEnd() {
                        for (int p = 0; p < pairs.size(); p++) {
                            int idx = idxs.get(p)[0];
                            String old = pairs.get(p)[0];
                            String neu = pairs.get(p)[1];
                            List<LdcInsnNode> sites = new ArrayList<>();
                            for (AbstractInsnNode n = instructions.getFirst(); n != null; n = n.getNext()) {
                                if (n instanceof LdcInsnNode && old.equals(((LdcInsnNode) n).cst)) {
                                    Integer pushed = pushedInt(prevReal(n));
                                    if (pushed != null && pushed == idx) sites.add((LdcInsnNode) n);
                                }
                            }
                            hits[p] = sites.size();
                            if (sites.size() == 1) sites.get(0).cst = neu;
                        }
                        accept(next);
                    }
                };
            }
        };
        cr.accept(cv, 0);
        if (clinits[0] != 1) throw new IllegalStateException("<clinit> found " + clinits[0] + " times");
        for (int p = 0; p < pairs.size(); p++) {
            System.out.println("PatchStrings: idx " + idxs.get(p)[0] + " '" + escape(pairs.get(p)[0]) + "' -> '"
                    + escape(pairs.get(p)[1]) + "': " + hits[p] + " site(s)");
            if (hits[p] != 1) throw new IllegalStateException("expected exactly 1 site for pair " + p + ", found " + hits[p]);
        }
        byte[] out = cw.toByteArray();
        Path op = Paths.get(a[1]);
        if (op.getParent() != null) Files.createDirectories(op.getParent());
        Files.write(op, out);
        System.out.println("PatchStrings: " + a[0] + " " + in.length + " -> " + a[1] + " " + out.length + " bytes");
    }
}
