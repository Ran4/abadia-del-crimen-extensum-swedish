import java.awt.*;
import java.awt.image.BufferedImage;

/** Prints the exact pixels Java2D sets for each accent overlay used by abadia.y (case 2). Headless. */
public class OverlayPixels {
    static int[][][] L = {
        // name order: v(acute) w(grave) x(circumflex) y(apostrophe) z(cedilla) C(ogonek) A(dot) B(stroke)
        {{2,1,4,0},{3,1,5,0}},
        {{4,1,2,0},{5,1,3,0}},
        {{2,0,4,2},{3,0,5,2},{2,0,0,2},{3,0,1,2}},
        {{0,3,1,1},{1,3,2,1}},
        {{0,15,3,13},{1,15,3,13}},
        {{4,13,3,14},{4,14,5,14}},
        {{4,1,3,1},{4,2,3,2}},
        {{0,8,4,6},{1,8,5,6}},
    };
    static String[] N = {"v_acute","w_grave","x_circumflex","y_apostrophe","z_cedilla","C_ogonek","A_dot","B_stroke"};
    public static void main(String[] a) {
        for (int k = 0; k < L.length; k++) {
            BufferedImage im = new BufferedImage(40, 40, BufferedImage.TYPE_INT_RGB);
            Graphics g = im.getGraphics();
            g.setColor(Color.WHITE); g.fillRect(0, 0, 40, 40);
            g.setColor(new Color(0xC0000000, true));
            int ox = 10, oy = 10;
            for (int[] l : L[k]) g.drawLine(ox + l[0], oy + l[1], ox + l[2], oy + l[3]);
            StringBuilder sb = new StringBuilder(N[k] + ":");
            for (int y = 0; y < 40; y++) for (int x = 0; x < 40; x++) {
                int rgb = im.getRGB(x, y) & 0xFFFFFF;
                if (rgb != 0xFFFFFF) sb.append(String.format(" (%d,%d,%02X)", x - ox, y - oy, rgb & 0xFF));
            }
            System.out.println(sb);
        }
    }
}
