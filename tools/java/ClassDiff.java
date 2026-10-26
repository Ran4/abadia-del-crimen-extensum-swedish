import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.*;
import java.util.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import org.objectweb.asm.util.Textifier;
import org.objectweb.asm.util.TraceMethodVisitor;

/**
 * Swedish build: structural comparison helpers for patched classes.
 *
 *   ClassDiff clinit-strings <x.class>
 *       prints every String constant that <clinit> stores into an array slot, as
 *       FIELD<TAB>INDEX<TAB>VALUE (VALUE escaped like PatchStrings: \\ \t \n \r \\uXXXX), where
 *       INDEX is the int pushed right before the LDC and FIELD the next PUTSTATIC target.
 *   ClassDiff samecode <orig.class> <new.class> [name+desc ...]
 *       asserts that the class header, fields and every method except the listed ones are
 *       identical (instructions compared as ASM Textifier listings, i.e. by value, not by pool
 *       index). Prints "SAMECODE OK" and the listed methods that did change; exit 1 otherwise.
 */
public class ClassDiff {

    static ClassNode read(String path) throws Exception {
        ClassNode cn = new ClassNode();
        new ClassReader(Files.readAllBytes(Paths.get(path))).accept(cn, 0);
        return cn;
    }

    static String text(MethodNode m) {
        Textifier t = new Textifier();
        TraceMethodVisitor tv = new TraceMethodVisitor(t);
        m.accept(tv);
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        t.print(pw);
        pw.flush();
        return m.access + " " + m.name + m.desc + " sig=" + m.signature + " exc=" + m.exceptions
                + " maxs=" + m.maxStack + "/" + m.maxLocals + "\n" + sw;
    }

    public static void main(String[] a) throws Exception {
        if (a.length >= 2 && a[0].equals("clinit-strings")) {
            ClassNode cn = read(a[1]);
            for (MethodNode m : cn.methods) {
                if (!m.name.equals("<clinit>")) continue;
                List<String> pending = new ArrayList<>();
                for (AbstractInsnNode n = m.instructions.getFirst(); n != null; n = n.getNext()) {
                    if (n instanceof LdcInsnNode && ((LdcInsnNode) n).cst instanceof String) {
                        Integer idx = PatchStrings.pushedInt(PatchStrings.prevReal(n));
                        if (idx != null) pending.add(idx + "\t" + PatchStrings.escape((String) ((LdcInsnNode) n).cst));
                    } else if (n.getOpcode() == Opcodes.PUTSTATIC) {
                        for (String p : pending) System.out.println(((FieldInsnNode) n).name + "\t" + p);
                        pending.clear();
                    }
                }
                for (String p : pending) System.out.println("?\t" + p);
            }
            return;
        }
        if (a.length >= 3 && a[0].equals("samecode")) {
            ClassNode o = read(a[1]);
            ClassNode n = read(a[2]);
            Set<String> allowed = new HashSet<>(Arrays.asList(a).subList(3, a.length));
            List<String> problems = new ArrayList<>();
            if (o.version != n.version) problems.add("version " + o.version + " -> " + n.version);
            if (o.access != n.access) problems.add("access " + o.access + " -> " + n.access);
            if (!o.name.equals(n.name)) problems.add("name");
            if (!Objects.equals(o.superName, n.superName)) problems.add("superName");
            if (!o.interfaces.equals(n.interfaces)) problems.add("interfaces");
            if (!Objects.equals(o.sourceFile, n.sourceFile)) problems.add("sourceFile");
            if (o.fields.size() != n.fields.size()) problems.add("field count " + o.fields.size() + " -> " + n.fields.size());
            for (int i = 0; i < Math.min(o.fields.size(), n.fields.size()); i++) {
                FieldNode x = o.fields.get(i), y = n.fields.get(i);
                if (x.access != y.access || !x.name.equals(y.name) || !x.desc.equals(y.desc)
                        || !Objects.equals(x.value, y.value) || !Objects.equals(x.signature, y.signature))
                    problems.add("field " + i + " " + x.name + x.desc + " differs");
            }
            Map<String, MethodNode> om = new LinkedHashMap<>(), nm = new LinkedHashMap<>();
            for (MethodNode m : o.methods) om.put(m.name + m.desc, m);
            for (MethodNode m : n.methods) nm.put(m.name + m.desc, m);
            if (!new ArrayList<>(om.keySet()).equals(new ArrayList<>(nm.keySet())))
                problems.add("method list differs: " + om.keySet() + " -> " + nm.keySet());
            List<String> changed = new ArrayList<>();
            for (String k : om.keySet()) {
                if (!nm.containsKey(k)) continue;
                boolean same = text(om.get(k)).equals(text(nm.get(k)));
                if (!same) {
                    if (allowed.contains(k)) changed.add(k);
                    else problems.add("method " + k + " changed");
                }
            }
            for (String k : allowed) if (!om.containsKey(k)) problems.add("listed method " + k + " not found");
            if (!problems.isEmpty()) {
                System.out.println("SAMECODE FAIL " + a[1] + " vs " + a[2] + ": " + problems);
                System.exit(1);
            }
            System.out.println("SAMECODE OK " + n.name + ": changed methods " + changed);
            return;
        }
        System.err.println("usage: ClassDiff clinit-strings <x.class> | samecode <orig> <new> [name+desc ...]");
        System.exit(1);
    }
}
