import csv


class Gun:
    """
    A naval gun, as mounted on a ship.

    Attributes:
        - caliber: the caliber of the gun in inches.
        - max_range: maximum range in yards.
        - long_to_hit: chance to hit per gun per minute at long range.
        - long_min: minimum range in yards considered to be long range.
        - effective_to_hit: chance to hit per gun per minute at effective range.
        - effective_min: minimum range in yards considered to be effective.
        - short_to_hit: chance to hit per gun per minute at short range.
        - active: whether the gun is active (True) or Out Of Action (False). All guns are initialised as active.
    """

    def __init__(self, caliber, max_range, long_to_hit, long_min, effective_to_hit, effective_min, short_to_hit):
        self.caliber = max(0, caliber)
        self.max_range = max_range
        self.long_to_hit = long_to_hit
        self.long_min = long_min
        self.effective_to_hit = effective_to_hit
        self.effective_min = effective_min
        self.short_to_hit = short_to_hit
        self.active = True

    def return_to_hit(self, target_range):
        """Return the chance to hit (per gun and minute) for a given range. If the target is out of range, return 0."""
        if target_range > self.max_range:
            return 0
        elif target_range > self.long_min:
            return self.long_to_hit
        elif target_range > self.effective_min:
            return self.effective_to_hit
        elif target_range >= 0:
            return self.short_to_hit
        else:
            raise ValueError("Range must be a positive integer")

    def return_damage_conversion_factor(self):
        """Return the conversion factor of a caliber to 6-inch hits (light guns) or 15-inch hits (heavy guns)"""
        # Conversion factor to 6-inch hits for light gun calibers
        if self.caliber <= 7.5:
            # The conversion factors below are as stated in the original 1921 rules
            if self.caliber == 4:
                damage_equivalent = 1/3
            elif self.caliber == 4.7:
                damage_equivalent = 1/2
            elif self.caliber == 6:
                damage_equivalent = 1
            elif self.caliber == 7.5:
                damage_equivalent = 3
            # All other light calibers are determined through interpolation
            # We used polynomial regression (R squared value of 0.9966)
            else:
                damage_equivalent = 1 / ((0.1746 * (self.caliber ** 2)) - (2.7523 * self.caliber) + 11.168)
        # Conversion factor to 15-inch hits for heavy gun calibers
        elif self.caliber > 7.5:
            # Here we just use an equation for all cases because damage for big guns scales linearly
            damage_equivalent = 1 / ((self.caliber/3) + 6)
        else:
            raise ValueError("Caliber must be a positive real number")

        return damage_equivalent

    def return_equivalent_damage(self, range):
        """Return the damage dealt by the gun over one minute at a given range, adjusted to 15-inch (capital guns)
        or 6-inch (light guns) equivalent hits."""
        equivalent_damage = self.return_to_hit(range) * self.return_damage_conversion_factor()
        return equivalent_damage

    def is_active(self):
        """Return True if the gun is active, False if it is Out Of Action."""
        return self.active

    def knock_out(self):
        """Knock the gun out (make it inactive). Caused by enemy fire."""
        self.active = False


class Ship:
    """
    A ship object. Keeps track of its damage status and contains gun objects.

    Attributes:
        Input from file:
        - name: the name of the ship (string).
        - hull_class: "battleship", "battle cruiser", "light cruiser", "flotilla leader" or "destroyer" (string).
        - main_armament_type: the model of gun used in the ship's main battery (gun object).
        - main_armament_count: the total number of guns of the main type carried by the ship (int).
        - main_armament_broadside: the number of guns the ship can bring to bear in either broadside (int).
        Calculated by the program:
        - staying_power: the ship's staying power (int).
            - For battleships and battle cruisers, measured in 15-inch hits.
            - For light cruisers and smaller classes, measured in 6-inch hits.
        - hit_points: begins equal to staying power. Used to keep track of damage (float).
        - status: 1 means undamaged, 0 means out of action / firepower kill (float).
    """

    def __init__(self, name, hull_class, main_armament_type, main_armament_count, main_armament_broadside):
        self.name = name
        self.hull_class = hull_class
        self.main_armament_type = main_armament_type
        self.main_armament_count = main_armament_count
        self.main_armament_broadside = main_armament_broadside
        self.staying_power = main_armament_count
        # Calculate the staying power multiplier for battleships based on main gun calibre.
        if self.hull_class == "battleship":
            if self.main_armament_type.caliber <= 12:
                self.staying_power *= 1
            elif self.main_armament_type.caliber <= 14:
                self.staying_power *= 2
            elif self.main_armament_type.caliber <= 15:
                self.staying_power *= 3
            else:
                self.staying_power *= 3.25
        # Calculate the staying power multiplier for battle cruisers based on main gun calibre.
        elif self.hull_class == "battle cruiser":
            if self.main_armament_type.caliber <= 12:
                self.staying_power *= 0.75
            elif self.main_armament_type.caliber <= 13.5:
                self.staying_power *= 1.75
            elif self.main_armament_type.caliber <= 15:
                self.staying_power *= 2.5
            else:
                self.staying_power *= 2.75
        # Calculate the staying power multiplier for light cruisers based on main gun calibre.
        elif self.hull_class == "light cruiser":
            if self.main_armament_type.caliber <= 4:
                self.staying_power *= 4
            elif self.main_armament_type.caliber <= 6:
                self.staying_power *= 8
            else:
                self.staying_power *= 9
        # Calculate the staying power multiplier for light squadron ships based on main gun calibre.
        elif self.hull_class in ("flotilla leader", "destroyer"):
            self.staying_power *= 1
            """Note that a value of 1 in the above line will not change staying power at all. The
            line is left here for clarity and in case one needs to experiment with the value."""
        # Raise an exception if attempting to create a ship without a valid hull class.
        else:
            raise ValueError("Wrong ship class definition")

        # Set the ship's initial hit points and status
        self.hit_points = self.staying_power
        self.status = 1


def build_gun_dictionary(filename):
    """Build a dictionary of gun parameters from an external CSV file:
        - Key: the gun designation (e.g. '13.5 in V' or '12 in XI')
        - Value: a list of parameters, in the order:
            * caliber (in inches)
            * max_ange (maximum range in yards)
            * long_to_hit (chance to hit per gun and minute at long range)
            * long_min (minimum range considered to be long)
            * effective_to_hit (chance to hit per gun and minute at effective range)
            * effective_min (minimum range considered to be effective)
            * short_to_hit (chance to hit per gun and minute at short range)
    """

    gun_dict = {}
    with open(filename) as sourcefile:
        reader = csv.reader(sourcefile, delimiter=",")
        next(reader)
        for row in reader:
            gun_data = list(row)
            gun_dict[gun_data[0]] = list(map(float, gun_data[1:]))
    return gun_dict


# Build the gun dictionary for capital ships
capital_guns = build_gun_dictionary("capital_ship_guns.csv")

# Build the gun dictionary for cruisers
cruiser_guns = build_gun_dictionary("light_cruiser_guns.csv")

# Build the gun dictionary for destroyers
destroyer_guns = build_gun_dictionary("destroyer_guns.csv")

# Build the gun dictionary for destroyers
secondary_guns = build_gun_dictionary("secondary_guns.csv")

# CREATE TEST GUNS AND GET THEIR TO HIT VALUE AT AN ARBITRARY RANGE
# Create the guns from the dictionary by their designation
four_inch_v = Gun(*destroyer_guns["4 in V"])
six_inch_xii = Gun(*cruiser_guns["6 in XII"])

# CREATE TEST SHIPS AND GET THEIR THE STAYING POWER
# Create the ships from manually input values
emden = Ship("SMS Emden", "light cruiser", four_inch_v, 10, 5)
sydney = Ship("HMAS Sydney", "light cruiser", six_inch_xii, 8, 5)
# Print the staying power for their class and armament type
print(emden.staying_power)
print(sydney.staying_power)
# Fire a test broadside at 10000 yards
print(emden.main_armament_type.return_to_hit(10000) * emden.main_armament_broadside)
print(sydney.main_armament_type.return_to_hit(10000) * sydney.main_armament_broadside)
