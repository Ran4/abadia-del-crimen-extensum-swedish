import java.nio.file.*;
import java.util.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

/**
 * Swedish build: add Å (and the lowercase insurance keys å ä ö) to the private glyph routine
 * abadia.j.a(IIILjava/awt/Graphics;)V. Port of work/phaseA/proto_font/src/PatchJ.java
 * (FORMAT §3.4, DECISIONS D5). The build runs it with "125 -2 1" and asserts the output md5
 * f197f5a3e4b9d1c553ede4194efc75af.
 *
 * usage: java -cp asm-9.7.1.jar:asm-tree-9.7.1.jar:. PatchJ <in j.class> <out j.class>
 *            [ringCode=125] [ringDy=-2] [lowercase=1] [breakFrame=0]
 *
 * Adds to the method's single lookupswitch:
 *   197 'Å' and 229 'å'  -> new block:  a(65, x, y, g); a(ringCode, x, y+ringDy, g); return;
 *   228 'ä' -> existing case target of 196 'Ä' (A + diaeresis)   [if lowercase=1]
 *   246 'ö' -> existing case target of 214 'Ö' (O + diaeresis)   [if lowercase=1]
 * Every other method is copied verbatim (ClassWriter(reader) copy path), the constant pool is
 * unchanged, so only this one method's Code attribute changes.
 *
 * Frames: the class is v51 and has a StackMapTable. The reader runs with flags 0 (compressed
 * frames pass through); the appended block follows an unconditional `return`, so it gets its own
 * explicit F_FULL frame matching the frames of the original case targets
 * (locals [TOP, I, I, Graphics, I, I, I, I, I, I], empty stack). No COMPUTE_FRAMES.
 * breakFrame=1 declares local 3 as INTEGER: a deliberately invalid class, used by the build as the
 * negative control that proves the -Xverify:all link step really verifies.
 */
public class PatchJ {
    static final String OWNER = "abadia/j";
    static final String NAME = "a";
    static final String DESC = "(IIILjava/awt/Graphics;)V";

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: PatchJ <in j.class> <out j.class> [ringCode=125] [ringDy=-2] [lowercase=1] [breakFrame=0]");
            System.exit(1);
        }
        byte[] in = Files.readAllBytes(Paths.get(args[0]));
        final int ringCode = args.length > 2 ? Integer.parseInt(args[2]) : 125;
        final int ringDy = args.length > 3 ? Integer.parseInt(args[3]) : -2;
        final boolean lower = args.length > 4 ? !args[4].equals("0") : true;
        final boolean breakFrame = args.length > 5 && args[5].equals("1");
        if (ringCode < 45 || ringCode > 127)
            throw new IllegalArgumentException("ring code must be a bipush-able glyph code 45..127");

        ClassReader cr = new ClassReader(in);
        if (cr.readShort(6) != 51) throw new IllegalStateException("expected class major version 51");
        ClassWriter cw = new ClassWriter(cr, 0);
        final int[] hits = {0};
        ClassVisitor cv = new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int acc, String name, String desc, String sig, String[] exc) {
                final MethodVisitor next = super.visitMethod(acc, name, desc, sig, exc);
                if (!(name.equals(NAME) && desc.equals(DESC))) return next; // verbatim copy
                hits[0]++;
                return new MethodNode(Opcodes.ASM9, acc, name, desc, sig, exc) {
                    @Override
                    public void visitEnd() {
                        transform(this, ringCode, ringDy, lower, breakFrame);
                        accept(next);
                    }
                };
            }
        };
        cr.accept(cv, 0);
        if (hits[0] != 1) throw new IllegalStateException("target method found " + hits[0] + " times");
        Files.write(Paths.get(args[1]), cw.toByteArray());
        System.out.println("PatchJ: patched " + OWNER + "." + NAME + DESC + " ring=" + ringCode + " dy=" + ringDy
                + " lowercase=" + lower + (breakFrame ? " (BROKEN FRAME negative control)" : ""));
    }

    static void transform(MethodNode m, int ringCode, int ringDy, boolean lower, boolean breakFrame) {
        LookupSwitchInsnNode sw = null;
        for (AbstractInsnNode n : m.instructions)
            if (n instanceof LookupSwitchInsnNode) {
                if (sw != null) throw new IllegalStateException("more than one lookupswitch");
                sw = (LookupSwitchInsnNode) n;
            }
        if (sw == null) throw new IllegalStateException("no lookupswitch");
        // Sanity: the method must be the one documented in FORMAT §3.2 (36 keys, 196/214 present, no 197).
        TreeMap<Integer, LabelNode> cases = new TreeMap<>();
        for (int i = 0; i < sw.keys.size(); i++) cases.put(sw.keys.get(i), sw.labels.get(i));
        if (cases.size() != 36 || !cases.containsKey(196) || !cases.containsKey(214)
                || cases.containsKey(197) || cases.containsKey(229) || cases.containsKey(ringCode))
            throw new IllegalStateException("unexpected switch keys " + cases.keySet());
        if (m.maxStack < 4 || m.maxLocals != 10)
            throw new IllegalStateException("unexpected maxs " + m.maxStack + "/" + m.maxLocals);

        LabelNode ring = new LabelNode();
        InsnList blk = new InsnList();
        blk.add(ring);
        Object[] locals = {Opcodes.TOP, Opcodes.INTEGER, Opcodes.INTEGER,
                breakFrame ? Opcodes.INTEGER : "java/awt/Graphics",
                Opcodes.INTEGER, Opcodes.INTEGER, Opcodes.INTEGER,
                Opcodes.INTEGER, Opcodes.INTEGER, Opcodes.INTEGER};
        blk.add(new FrameNode(Opcodes.F_FULL, locals.length, locals, 0, new Object[0]));
        // a(65 /*'A'*/, x, y, g)
        blk.add(new IntInsnNode(Opcodes.BIPUSH, 65));
        blk.add(new VarInsnNode(Opcodes.ILOAD, 1));
        blk.add(new VarInsnNode(Opcodes.ILOAD, 2));
        blk.add(new VarInsnNode(Opcodes.ALOAD, 3));
        blk.add(new MethodInsnNode(Opcodes.INVOKESTATIC, OWNER, NAME, DESC, false));
        // a(ringCode, x, y + ringDy, g)
        if (Math.abs(ringDy) > 5) throw new IllegalArgumentException("|ringDy| must be <= 5 (iconst)");
        blk.add(new IntInsnNode(Opcodes.BIPUSH, ringCode));
        blk.add(new VarInsnNode(Opcodes.ILOAD, 1));
        blk.add(new VarInsnNode(Opcodes.ILOAD, 2));
        blk.add(new InsnNode(Opcodes.ICONST_0 + Math.abs(ringDy)));
        blk.add(new InsnNode(ringDy < 0 ? Opcodes.ISUB : Opcodes.IADD));
        blk.add(new VarInsnNode(Opcodes.ALOAD, 3));
        blk.add(new MethodInsnNode(Opcodes.INVOKESTATIC, OWNER, NAME, DESC, false));
        blk.add(new InsnNode(Opcodes.RETURN));
        // The method's last instruction is `return`, so the appended block is reachable only
        // through the new switch keys.
        AbstractInsnNode last = m.instructions.getLast();
        while (last != null && last.getOpcode() < 0) last = last.getPrevious();
        if (last == null || last.getOpcode() != Opcodes.RETURN)
            throw new IllegalStateException("method does not end in RETURN");
        m.instructions.add(blk);

        cases.put(197, ring);
        cases.put(229, ring);
        if (lower) {
            cases.put(228, cases.get(196));
            cases.put(246, cases.get(214));
        }
        sw.keys.clear();
        sw.labels.clear();
        for (Map.Entry<Integer, LabelNode> e : cases.entrySet()) { // TreeMap => ascending keys
            sw.keys.add(e.getKey());
            sw.labels.add(e.getValue());
        }
    }
}
