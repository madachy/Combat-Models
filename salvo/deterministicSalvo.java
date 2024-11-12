import java.util.ArrayList;
import java.util.List;

/**
 * A Java implementation of the Deterministic Salvo Model created by Wayne P. Hughes Jr.
 * Converted from Python implementation by Alvaro Radigales.
 */
public class NavalWarfareSimulation {

    public static class Ship {
        private String type;
        private int op;    // anti-ship cruise missiles
        private int dp;    // SAM missiles
        private double sp; // initial staying power
        private double hp; // current hit points
        private double status; // fraction of staying power remaining

        public Ship(String type, int op, int dp, double sp) {
            this.type = type;
            this.op = op;
            this.dp = dp;
            this.sp = sp;
            this.hp = sp;
            this.status = 1.0;
        }

        public void damage(double damage) {
            damage = Math.min(damage, hp);
            damage = Math.max(damage, 0);
            hp -= damage;
            status = hp / sp;
        }

        public double ascmFire() {
            return op * status;
        }

        public double samFire() {
            return dp * status;
        }

        @Override
        public String toString() {
            double shipStatus = Math.round(status * 10000.0) / 100.0;
            double shipOp = Math.round(ascmFire() * 100.0) / 100.0;
            double shipDp = Math.round(samFire() * 100.0) / 100.0;
            return String.format("%s (%.2f%%) OP: %.2f DP: %.2f", 
                type, shipStatus, shipOp, shipDp);
        }
    }

    public static class Missiles {
        private double launchReliability;
        private double ascmToHit;
        private double samToHit;

        public Missiles() {
            this(1.0, 1.0, 1.0);
        }

        public Missiles(double launchReliability, double ascmToHit, double samToHit) {
            this.launchReliability = launchReliability;
            this.ascmToHit = ascmToHit;
            this.samToHit = samToHit;
        }

        public double offensiveModifier() {
            return launchReliability * ascmToHit;
        }

        public double getSamToHit() {
            return samToHit;
        }
    }

    public static class Group {
        private String side;
        private List<Ship> oob; // order of battle
        private double scouting;
        private double readiness;
        private Missiles missiles;

        public Group(String side, Ship ship, int units, double scouting, double readiness, Missiles missiles) {
            this.side = side;
            this.oob = new ArrayList<>();
            for (int i = 0; i < units; i++) {
                oob.add(new Ship(ship.type, ship.op, ship.dp, ship.sp));
            }
            this.scouting = scouting;
            this.readiness = readiness;
            this.missiles = missiles;
        }

        public double strikingPower() {
            double salvoSize = oob.stream().mapToDouble(Ship::ascmFire).sum();
            return salvoSize * scouting * missiles.offensiveModifier();
        }

        public double defensivePower() {
            double defensiveSalvoSize = oob.stream().mapToDouble(Ship::samFire).sum();
            return defensiveSalvoSize * readiness;
        }

        public double combatPower(Group enemy) {
            double overwhelm = Math.max(strikingPower() - enemy.defensivePower(), 0);
            if (overwhelm > 0) {
                return overwhelm + (1 - enemy.missiles.getSamToHit()) * enemy.defensivePower();
            } else {
                return (1 - enemy.missiles.getSamToHit()) * strikingPower();
            }
        }

        public double totalStatus() {
            return oob.stream().mapToDouble(ship -> ship.status).sum();
        }

        public void damage(double damage) {
            while (damage > 0 && totalStatus() > 0) {
                for (Ship ship : oob) {
                    if (ship.status > 0) {
                        if (damage > ship.hp) {
                            damage -= ship.hp;
                            ship.damage(ship.hp);
                        } else {
                            ship.damage(damage);
                            damage = 0;
                        }
                    }
                }
            }
        }

        @Override
        public String toString() {
            double percentage = Math.round((totalStatus() / oob.size()) * 10000.0) / 100.0;
            double activeShips = Math.round(totalStatus() * 100.0) / 100.0;
            return String.format("%s: %.2f%% (%.2f active ships)", side, percentage, activeShips);
        }
    }

    public static class Battle {
        private Group blu;
        private Group red;
        private int duration;
        private int pulse;

        public Battle(Group blu, Group red, int duration) {
            this.blu = blu;
            this.red = red;
            this.duration = duration;
            this.pulse = 0;
        }

        public Battle(Group blu, Group red) {
            this(blu, red, 0);
        }

        public boolean stalemate() {
            return blu.combatPower(red) == 0 && red.combatPower(blu) == 0;
        }

        public void bluSurprise() {
            if (pulse == 0) {
                System.out.printf("%nBattle starts between %s and %s%n%n", blu.side, red.side);
                System.out.println(this);
            }
            pulse++;
            red.damage(blu.combatPower(red));
            System.out.println(this);
        }

        public void redSurprise() {
            if (pulse == 0) {
                System.out.printf("%nBattle starts between %s and %s%n%n", blu.side, red.side);
                System.out.println(this);
            }
            pulse++;
            blu.damage(red.combatPower(blu));
            System.out.println(this);
        }

        public void salvo() {
            if (pulse == 0) {
                System.out.printf("%nBattle starts between %s and %s%n%n", blu.side, red.side);
                System.out.println(this);
            }
            double bluDamageSustained = red.combatPower(blu);
            double redDamageSustained = blu.combatPower(red);
            blu.damage(bluDamageSustained);
            red.damage(redDamageSustained);
            pulse++;
            System.out.println(this);
        }

        public void resolve() {
            if (duration == 0) {
                while (blu.totalStatus() != 0 && red.totalStatus() != 0) {
                    salvo();
                    if (stalemate()) {
                        System.out.println("\nStalemate! Neither fleet can penetrate enemy missile defence.");
                        break;
                    }
                }
            } else {
                for (int i = 0; i < duration; i++) {
                    salvo();
                }
            }
        }

        @Override
        public String toString() {
            return String.format("%nPulse %d:%n%s | %s", pulse, blu, red);
        }
    }

    public static void main(String[] args) {
        // Test battle scenario taken from Tiah, Yao Ming (2007), excursion A3, pp. 26-29
        Ship frigate = new Ship("Frigate", 8, 6, 1.5);
        Ship corvette = new Ship("Corvette", 4, 2, 1.0);

        // String override demo
        System.out.println(frigate);
        System.out.println(corvette);

        // Anti-Ship Cruise Missiles and SAM used by both groups
        Missiles standard = new Missiles(0.9, 0.7, 0.68);

        // Group creation
        Group blufor = new Group("BLUFOR", frigate, 4, 0.6, 1.0, standard);
        Group redfor = new Group("REDFOR", corvette, 12, 0.6, 1.0, standard);

        // Battle creation, no duration specified
        Battle battle = new Battle(blufor, redfor);

        // Battle resolves until one side is wiped out
        battle.resolve();
    }
}
