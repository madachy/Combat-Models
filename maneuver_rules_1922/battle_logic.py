#########################################
# NAVAL WAR COLLEGE MANEUVER RULES 1922 #
#########################################

# import math
import os
import pandas as pd


FIRE_EFFECT_TABLES_EDITION = "1930"


class Gun:
    """A naval gun. All parameters are loaded from external data files upon object creation.

    The following Class variables exist, containing information relevant to all Gun instances:
    - general_data (DataFrame): a table listing the caliber, projectile weight, muzzle velocity and maximum range of all
    gun denominations, as well as the navies in which they saw service.
    - penetrative_values (DataFrame): a table listing the multipliers needed to convert penetrative hits from every
    caliber to equivalent 14-inch hits.
    - non_penetrative_values (DataFrame): a table listing the multipliers needed to convert non-penetrative hits from
    every caliber to equivalent 14-inch hits.
    - rate_of_fire (DataFrame): a table listing the rates of fire of all gun designations at all ranges (in 1000-yard
    increments).

    Instance variables are documented in the constructor method docstring.
    """

    # GUN TYPES
    # Load the CSV file containing general data for all gun designations.
    gun_types_path = "fire_effect_tables/{}/gun_types.csv".format(FIRE_EFFECT_TABLES_EDITION)
    general_data = pd.read_csv(gun_types_path, index_col="designation", na_values="--")

    # HIT VALUE CONVERSION FACTORS
    # Define the paths for the hit value tables.
    penetrative_path = "fire_effect_tables/{}/hit_values_penetrative.csv".format(FIRE_EFFECT_TABLES_EDITION)
    non_penetrative_path = "fire_effect_tables/{}/hit_values_non_penetrative.csv".format(FIRE_EFFECT_TABLES_EDITION)
    # Load the data.
    penetrative_values = pd.read_csv(penetrative_path, index_col="caliber", dtype=float)
    non_penetrative_values = pd.read_csv(non_penetrative_path, index_col="caliber", dtype=float)

    # RATE OF FIRE
    # Define the path for the rates of fire table.
    rates_of_fire_path = "fire_effect_tables/{}/rates_of_fire.csv".format(FIRE_EFFECT_TABLES_EDITION)
    # Create a rate of fire dataframe.
    rate_of_fire = pd.read_csv(rates_of_fire_path, index_col='range', na_values="--", dtype=float)

    def __init__(self, gun_designation):
        """All parameters for each individual gun are loaded from external CSV files and calculated upon creation of
        each instance. The only necessary parameter to create a gun is its designation, following the format:

        [caliber]-in-[length]

        For example, '6-in-50' means the 6-inch/50 gun.
         
        Guns in AA mounts append '-A' to the designation (e.g. '4-in-45-A' is the 4-inch/45 AA gun).
         
        Parameters:
            - gun_designation (string): the text string of the gun's designation as described above.
             
        Attributes:
            - caliber (float): the gun's caliber in inches.
            - projectile_weight (float): the projectile weight in lbs.
            - muzzle_velocity (int): the muzzle velocity in feet per second.
            - maximum_range (int): the gun's maximum range in thousands of yards.
            - hit_percentage (dict): a dictionary of Pandas DataFrames listing the gun's hit percentages at different
              firing ranges (in 1000-yard intervals) and for different target sizes ("large", "intermediate", "small",
              "destroyer" and "submarine". The dictionary keys are the different spot types ("top", "kite" and "plane").
              Note that only the 1922 revision of the rules uses kite spot.
            - side_penetration_ranges (DataFrame): a table listing the range limits for side (belt) penetration of
              various armor thicknesses.
            - deck_penetration_ranges (DataFrame): a table listing the range limits for deck penetration of various
              armor thicknesses. Only applies to guns 5.5 inches in caliber or greater.
        """

        self.designation = gun_designation
        # Define the path for the gun's fire effect tables
        fire_effect_tables_path = "fire_effect_tables/{}/{}/".format(FIRE_EFFECT_TABLES_EDITION, gun_designation)

        # GENERAL DATA

        self.caliber = float(self.designation.split("-")[0])

        # Fill out the gun's general data.
        self.projectile_weight = int(Gun.general_data["projectile_weight"][self.designation])
        self.muzzle_velocity = int(Gun.general_data["muzzle_velocity"][self.designation])
        self.maximum_range = int(Gun.general_data["maximum_range"][self.designation])

        # HIT PERCENTAGE

        # Define the paths for the hit percentage tables under different spot conditions.
        top_spot_path = "{}{}_percent_{}.csv".format(fire_effect_tables_path, self.designation, "top")
        kite_spot_path = "{}{}_percent_{}.csv".format(fire_effect_tables_path, self.designation, "kite")
        plane_spot_path = "{}{}_percent_{}.csv".format(fire_effect_tables_path, self.designation, "plane")
        # Create a hit percentage dictionary containing all the existing hit percentage tables.
        self.hit_percentage = {}
        if os.path.exists(top_spot_path):
            self.hit_percentage["top"] = pd.read_csv(top_spot_path, index_col='range', na_values="--", dtype=float)
        if os.path.exists(kite_spot_path):
            self.hit_percentage["kite"] = pd.read_csv(kite_spot_path, index_col='range', na_values="--", dtype=float)
        if os.path.exists(plane_spot_path):
            self.hit_percentage["plane"] = pd.read_csv(plane_spot_path, index_col='range', na_values="--", dtype=float)

        # armor PENETRATION

        # Define the path for the side armor penetration ranges table.
        side_penetration_ranges_path = "{}{}_side_penetration_ranges.csv".format(fire_effect_tables_path,
                                                                                 self.designation)
        # Create a side penetration ranges dataframe.
        self.side_penetration_ranges = pd.read_csv(side_penetration_ranges_path, index_col='armor', na_values='---',
                                                   dtype=float)
        # Define the path for the deck penetration ranges table.
        if self.caliber >= 5.5:
            deck_penetration_ranges_path = "{}{}_deck_penetration_ranges.csv".format(fire_effect_tables_path,
                                                                                     self.designation)
            # Create a deck penetration ranges dataframe.
            self.deck_penetration_ranges = pd.read_csv(deck_penetration_ranges_path, index_col='armor', na_values='X',
                                                       dtype=float)

    def return_hit_percentage(self, target_size, target_range, spot_type):
        """Returns the hit percentage of the gun for a given target size, range and spot type.
        
        Parameters:
            - target_size (string): the size of the target ("large", "intermediate", "small", "destroyer" or
              "submarine").
            - target_range (int): the range to the target in thousands of yards.
            - spot_type (string): the type of spot used ("top", "plane" or "kite").
            
        Returns: the hit percentage (float).
        """
        target_range = int(target_range)
        if target_range > self.maximum_range:
            return 0
        if not target_range % 2:
            return self.hit_percentage[spot_type][target_size][target_range] / 100
        else:
            shorter_range = self.hit_percentage[spot_type][target_size][target_range - 1]
            longer_range = self.hit_percentage[spot_type][target_size][target_range + 1]
            return (shorter_range + longer_range) / 2 / 100

    def return_rate_of_fire(self, target_range):
        """Returns the rate of fire for the gun at a given range.
        
        Parameters:
            - target_range (int): the range to the target in thousands of yards.
            
        Returns: the rate of fire at the range given (float).
        """
        if target_range > self.maximum_range:
            return 0
        else:
            return Gun.rate_of_fire[self.designation][target_range]

    def return_hit_value(self, target_size, penetrative):
        """Returns the multiplier needed to convert a hit from the gun to the 14-inch hit equivalent.
        
        Attributes:
            - penetrative (boolean): whether the hit is penetrative or not.
        
        Returns: the conversion factor (float).    
        """
        
        if penetrative:
            if target_size == "submarine":
                return Gun.penetrative_values[target_size][self.caliber]
            else:
                return Gun.penetrative_values["large, intermediate, small, destroyer"][self.caliber]

        else:
            return Gun.non_penetrative_values[target_size][self.caliber]

    def return_side_penetration(self, armor, incidence, target_range):
        """Returns whether the gun would penetrate the side (belt) armor of a target.
        
        Parameters:
            - armor (float): the target's side armor in inches.
            - incidence (int): the shot incidence in degrees. Converted to 15-degree increments within the method.
            - target_range (int): the range to the target in thousands of yards.
            
        Returns: True if the shot penetrates, False if it does not.
        """
        
        # If armor is thicker than the range tables predict, return False.
        armor_values = self.side_penetration_ranges.index
        if armor > max(armor_values):
            return False

        # Else.
        # Round to the nearest 15 degrees and obtain the appropriate column.
        if incidence > 90:
            incidence -= (incidence // 90) * 90

        incidence = round(incidence / 15) * 15
        if incidence == 90 or incidence == 0:
            incidence = "90 or 0"
        elif incidence == 75 or incidence == 15:
            incidence = "75 or 15"
        elif incidence == 60 or incidence == 30:
            incidence = "60 or 30"
        else:
            incidence = "45"

        # Check for nearest armor value.
        if armor not in armor_values:
            armor = min(armor_values, key=lambda x: abs(x-armor))

        # Check whether a shot would penetrate at that range and incidence.
        if pd.isnull(self.side_penetration_ranges.loc[armor, incidence]):
            return True

        if target_range <= self.side_penetration_ranges.loc[armor, incidence]:
            return True

        else:
            return False

    def return_deck_penetration(self, armor, target_range):
        """Returns whether the gun would penetrate the deck armor of a target.
        
        Attributes:
            - armor (float): the target's deck armor in inches.
            - target_range (int): the range to the target in thousands of yards.
        """
        
        # Deck penetration only applies to guns 5.5 inches or larger.
        if self.caliber < 5.5:
            return False

        else:
            armor_values = self.deck_penetration_ranges.index
            # Return false if the armor is thicker than what is listed in the penetration tables.
            if armor > max(armor_values):
                return False
            # Likewise, return True if the armor is thinner than the minimum value listed.
            if armor < min(armor_values):
                return True

            # Else.
            # Check for the nearest armor value.
            if armor not in armor_values:
                armor = min(armor_values, key=lambda x: abs(x - armor))

            # Return false if the range listed for that armor value is NAN.
            if pd.isnull(self.deck_penetration_ranges.loc[armor, "target_range"]):
                return False

            # Else.
            if target_range >= self.deck_penetration_ranges.loc[armor, "target_range"]:
                return True

            else:
                return False


class Battery:
    """A battery of guns of the same caliber. Batteries are defined by their gun designation and caliber, the type of
    battery (primary, secondary or tertiary), the total number of mounts on the ship and their type (turret, casemate),
    the number of guns per mount, whether the battery has a low freeboard, and the number of mounts bearing on each arc
    (bow, broadside or stern) as well as the angle from the bow and stern defining those arcs.
    """

    def __init__(self, gun_type, battery_type, mount_type, total_mounts, bow_mounts, broadside_mounts, stern_mounts,
                 end_arc, guns_per_mount, low_freeboard=False):
        """All parameters are loaded automatically from external files (in particular from the fleet lists).

        Parameters:
            - gun_type (Gun object): a Gun object of the type used in the gun_battery.
            - battery_type (string): "primary", "secondary" or "tertiary". Fire events decide which guns are firing
              according to these categories. Note that ships having guns of the same caliber in different mount types
              (for example the 1906 Scharnhorst class, with four 8.3-inch guns in two centerline turrets and another
              four in broadside casemates) can have more than one battery of the same type (in this case, two different
              primary batteries in different mounts).
            - mount_type (string): "deck" or "broadside". May affect rate of fire in some versions of the rules.
            - total_mounts (int): the total number of mounts present in the gun_battery.
            - bow_mounts (int): the number of mounts bearing on the bow arc.
            - broadside_mounts (int): the number of mounts bearing on the broadside arc.
            - stern_mounts (int): the number of mounts bearing on the stern arc.
            - end_arc (int): the angle (in degrees) from the bow or stern at which the firing arc changes.
            - guns_per_mount (int): the number of guns per mount.
            - low_freeboard (bool): whether the guns are considered to be mounted low and close to the waterline. Guns
              thus mounted cannot fire in rough seas. Defaults to 'False'.

        Attributes:
            - caliber (float): the gun_battery's caliber, extracted from the gun type.
        """
        self.gun_type = gun_type
        self.caliber = gun_type.caliber
        self.battery_type = battery_type
        self.mount_type = mount_type
        self.total_mounts = total_mounts
        self.bow_mounts = bow_mounts
        self.broadside_mounts = broadside_mounts
        self.stern_mounts = stern_mounts
        self.end_arc = end_arc
        self.guns_per_mount = guns_per_mount
        self.low_freeboard = low_freeboard

        # Target data.
        self.target_data = pd.DataFrame(columns=["target_name", "firing_arc", "target_range", "side_penetration",
                                                 "deck_penetration", "allocated_mounts", "first_correction",
                                                 "second__correction"])

    def calculate_firing_arc(self, target_bearing):
        if target_bearing > 180:
            target_bearing = 180 - (target_bearing % 180)
        if target_bearing < self.end_arc:
            return "bow"
        elif target_bearing > (180 - self.end_arc):
            return "stern"
        else:
            return "broadside"

    def calculate_mounts_bearing(self, firing_arc):
        if firing_arc == "bow":
            return self.bow_mounts
        elif firing_arc == "stern":
            return self.stern_mounts
        else:
            return self.broadside_mounts

    def calculate_salvo_size(self, firing_arc):
        mounts_bearing = self.calculate_mounts_bearing(firing_arc)
        return mounts_bearing * self.guns_per_mount

    def target(self, ship_dictionary, target_name, target_range, target_bearing, shell_incidence_angle):
        # Calculate deck and side penetration.
        target_side_armor = ship_dictionary[target_name].side
        target_deck_armor = ship_dictionary[target_name].deck
        side_penetration = self.gun_type.return_side_penetration(target_side_armor, shell_incidence_angle, target_range)
        deck_penetration = self.gun_type.return_deck_penetration(target_deck_armor, target_range)

        # Calculate the firing arc.
        firing_arc = self.calculate_firing_arc(target_bearing)
        self.target_data.loc[target_name] = (target_name, firing_arc, target_range, side_penetration,
                                             deck_penetration, 0, 0, 0)

    def allocate_mounts(self):
        """Distribute the available gun mounts among the targets in the battery's target_data. The criteria followed:

        * If the bow or stern arcs are engaged, these take one mount away from the broadside arc.
        * In a first pass, the mounts are distributed uniformly among the targets using integer division. For example,
        distributing 7 mounts among 5 targets, the method will allocate 7 // 5 = 1 mount per target, with a remainder
        of two. Note how, should there be more targets than mounts, this first pass will assign 0 mounts per target.
        * Any mounts remaining are allocated one by one to the targets in the order they were targeted, until no more
        turrets are left.
        """
        firing_arcs = self.target_data['firing_arc'].tolist()
        bow_targets = stern_targets = 0
        # Check whether the bow arc is engaged.
        remaining_bow_mounts = remaining_stern_mounts = remaining_broadside_mounts = 0

        if "bow" in firing_arcs:
            bow_mounts = self.bow_mounts
            bow_targets = self.target_data["firing_arc"].value_counts()['bow']
            bow_mounts_per_target = bow_mounts // bow_targets
            remaining_bow_mounts = bow_mounts % bow_targets
            self.target_data.loc[(self.target_data["firing_arc"] == "bow"),
                                 "allocated_mounts"] = bow_mounts_per_target

        # Check whether the stern arc is engaged.
        if "stern" in firing_arcs:
            stern_mounts = self.stern_mounts
            stern_targets = self.target_data["firing_arc"].value_counts()["stern"]
            # Allocate turrets to all targets in a stern arc.
            stern_mounts_per_target = stern_mounts // stern_targets
            remaining_stern_mounts = stern_mounts % stern_targets
            self.target_data.loc[(self.target_data["firing_arc"] == "stern"),
                                 "allocated_turrets"] = stern_mounts_per_target

        # Check whether the broadside is engaged. Remove one turret from it if either bow or stern are engaged, two
        # if both are engaged.
        if "broadside" in firing_arcs:
            broadside_mounts = self.broadside_mounts
            if bow_targets > 0:
                broadside_mounts -= 1
            if stern_targets > 0:
                broadside_mounts -= 1
            broadside_targets = self.target_data["firing_arc"].value_counts()["broadside"]
            # Allocate turrets to all targets in a broadside arc.
            broadside_mounts_per_target = broadside_mounts // broadside_targets
            remaining_broadside_mounts = broadside_mounts % broadside_targets
            self.target_data.loc[(self.target_data["firing_arc"] == "broadside"),
                                 "allocated_mounts"] = broadside_mounts_per_target

        # Iterate over the dataframe allocating the remaining turrets.
        for i, row in self.target_data.iterrows():
            if row['firing_arc'] == "bow" and remaining_bow_mounts > 0:
                self.target_data.at[i, 'allocated_turrets'] += 1
                remaining_bow_mounts -= 1
            if row['firing_arc'] == "stern" and remaining_stern_mounts > 0:
                self.target_data.at[i, 'allocated_turrets'] += 1
                remaining_stern_mounts -= 1
            if row['firing_arc'] == "broadside" and remaining_broadside_mounts > 0:
                self.target_data.at[i, 'allocated_turrets'] += 1
                remaining_broadside_mounts -= 1


class Ship:
    """A naval ship. All the data needed to instantiate a new Ship object can be found in the corresponding fleet list
    data files.
    """

    def __init__(self, name, hull_class, size, life, side, deck):
        """Parameters:

            *General*
            - name (string): the name of the ship.
            - hull class (string): BB, CC, CA, CL, DD, etc. For a list of all possible values check the file
              'life_coefficients' in the 'helper_functions/' directory.
            - size (string): large, intermediate, small, destroyer or submarine.
            - side (float): the side (belt) armor amidships, in inches.
            - deck (float): the deck armor amidships, in inches.

            *Primary armament*
            - primary_fire_effect_table (string): the fire effect table used by the primary armament (e.g. "6-in-50").
            - primary_total (int): the number of turrets in the main gun_battery.
            - primary_broadside (int): the number of turrets the ship can fire broadside-on.
            - primary_bow (int): the number of turrets the ship can fire at a target ahead.
            - primary_stern (int): the number of turrets the ship can fire at a target astern.
            - primary_mount (int): the number of guns per turret in the ship's primary armament.
            - primary_end_arc (int): the number of degrees from the bow or stern before the firing arc is considered to
            be broadside-on.

            *Secondary armament*
            As above, except with secondary_ as a prefix.

            *Torpedoes*
            - torpedoes_type (string): the type and caliber of the torpedoes carried by the ship, if any.
            - torpedoes_mount (string): whether the torpedo tubes are submerged (S) or deck-mounted (D).
            - torpedoes_total (int): total number of torpedo tubes.
            - torpedoes_side (int): number of torpedo tubes which can fire on either side.

        Attributes:
            *Life*
            - hit_points (float): starts with the same value as the 'life' parameter and gets reduced by damage.
            - starting_hit_points (float): starts with the same value as the 'hit_points' attribute above, but
              represents the ship's hit points at the start of a three-minute move. At the end of the move, and after
              all gunnery damage has been subtracted from the 'hit_points' attribute, 'starting_hit_points' is updated
              with the value of the attribute 'hit_points'.
            - status (fraction): the total fraction remaining of the ship's life. Defined as the ship's hit points
              divided by its original life value. It affects gunnery, and is updated at the end of every move.

            *Motion*
            - initial_speed / current_speed (float): the speed in knots at the end of the last move, and at the start
              of the current move. Used to track ship acceleration and deceleration as it affects gunnery.
            - initial_course / current_course (int): the ship's course at the end of the last move, and at the start of
              the current move. Used to track changes of course (of firing and target ships) which may affect gunnery.

            *Targeting*
            - previous_target_data / target_data (DataFrames): tables containing the relevant data of all of the ship's
              targets, used to calculate fire corrections. Upon initialisation these DataFrames are empty, and they are
              populated through the Ship.target() method.
        """

        # General data
        self.name = name
        self.hull_class = hull_class
        self.size = size
        self.life = self.hit_points = self.starting_hit_points = life
        self.status = self.hit_points / self.starting_hit_points
        self.side = side
        self.deck = deck

        # Armament data
        self.primary_batteries = []
        self.secondary_batteries = []
        self.tertiary_batteries = []

        # Torpedo tubes might be implemented in the future.
        self.torpedoes = []

        # Own motion data
        self.initial_speed = self.current_speed = None
        self.initial_course = self.current_course = None

        # Target data
        self.remainder_hits = 0

        self.previous_target_data = pd.DataFrame(columns=["firing_group", "target_group", "target_name", "fire",
                                                          "armament_type", "target_range", "target_bearing", "evasive",
                                                          "shell_incidence_angle"])
        self.target_data = pd.DataFrame(columns=["firing_group", "target_group", "target_name", "fire", "armament_type",
                                                 "target_range", "target_bearing", "evasive", "shell_incidence_angle"])

        # Incoming fire data
        self.incoming_fire = pd.DataFrame(columns=["ship_name", "guns_firing", "caliber", "range"])

    def add_gun_battery(self, gun_battery):
        if gun_battery.battery_type == "primary":
            self.primary_batteries.append(gun_battery)
        elif gun_battery.battery_type == "secondary":
            self.secondary_batteries.append(gun_battery)
        elif gun_battery.battery_type == "tertiary":
            self.tertiary_batteries.append(gun_battery)

    def add_torpedoes(self, torpedoes):
        self.torpedoes.append(torpedoes)

    def target(self, ship_dictionary, firing_group, target_group, target_ships, fire, armament_types, target_range,
               target_bearing, evasive, shell_incidence_angle):
        """Add a target to the ship's target_data DataFrame. Additionally, register the firing ship in the target's
        'taking_fire_from' DataFrame. Eventually this will be done automatically from a battle's fire events CSV files.

        Parameters:
            - firing_side (string): either "side_a" or "side_b". The method will look for the firing group in the
              corresponding side's group dictionary.
            - firing_group (string): the name of the firing group.
            - target_group (string): the name of the group being targeted.
            - target_ships (list): the names of the ships being targeted. A single target will be a list of length one.
            - fire (boolean): whether the target is being fired at (True) or just tracked (False).
            - target_range (int): the range to the target in thousands of yards.
            - target_bearing (int): the target bearing in degrees.
            - evasive (boolean): whether the target is doing evasive maneuvers, defined as turning to both sides within
              the duration of one move (three minutes).
            - shell_incidence_angle (int): the shot incidence in degrees, used to determine whether the shots would be
              penetrating.
        """
        target_list = []
        for ship in target_ships:
            target_list.append(ship_dictionary[ship])

        for ship in target_list:
            self.target_data.loc[ship.name] = (firing_group, target_group, ship.name, fire, armament_types,
                                               target_range, target_bearing, evasive, shell_incidence_angle)

        # PASS THE TARGETING DATA TO THE BATTERIES.

        # Make a list of the armament types used against the target.
        # Check whether the target is being fired at.
        if fire:
            armament_types = [armament_type.strip() for armament_type in armament_types.split(',')]

            # Pass the target information to the batteries belonging to each armament as needed.
            if "primary" in armament_types:
                for gun_battery in self.primary_batteries:
                    for ship in target_list:
                        gun_battery.target(ship_dictionary, ship.name, target_range, target_bearing,
                                           shell_incidence_angle)

    def return_first_correction(self, target):
        """Returns the first correction to gunfire – a ratio which reduces rate of fire. It begins at a value of 1
        (no reduction) and diminishes in steps of one tenth depending on circumstances affecting gunnery. The factors
        taken into account are:

        * Ship status: a ship that has suffered damage will have its rate of fire reduced by the same proportion.
        * If opening fire, either because the target had not been fired at before, or because fire had been interrupted
        for three minutes or longer, a penalty is applied ranging between two tenths (20% reduction) and unity (no fire
        possible) depending on the range to the target.
        * If fire is shifted to a target in close formation with the previous one (and if the above rule does not apply)
        rate of fire is reduced by a flat three tenths.

        Returns: the first correction as a ratio (0 to 1) applied to rate of fire.
        """

        # The first correction starts at 1.
        first_correction = 1

        # F-49: Modify rate of fire by ship status.
        # status_lost = round(1 - math.ceil(self.status * 10) / 10, 1)
        # first_correction -= status_lost
        first_correction *= self.status

        # F-15: Check whether range has to be established.
        # First check whether the target has been fired at before for one full move.
        if (target not in self.previous_target_data.index or
                (target in self.previous_target_data.index and not self.previous_target_data["fire"][target])):
            target_group = self.target_data["target_group"][target]
            if ((self.previous_target_data['target_group'] == target_group) &
               self.previous_target_data['fire']).any():
                print("Fire shifted!")
                first_correction -= 0.3

            else:
                print("Opening fire!")
                # Keep track of whether fire is being opened, as it affects other rules.
                # opening_fire = True
                target_range = self.target_data["target_range"][target]
                if target_range > 25:
                    first_correction -= 1
                elif target_range >= 21:
                    first_correction -= 0.8
                elif target_range >= 16:
                    first_correction -= 0.6
                elif target_range >= 11:
                    first_correction -= 0.4
                elif target_range >= 6:
                    first_correction -= 0.2

        # F-18: Check whether fire has been obscured for less than one move, and if so reduce firepower proportionally.
        # This rule is not implemented directly. If anything has interfered with rate of fire for less than three
        # minutes during a given move, it should be specified in the "first correction modifier" for the event in the
        # fire events files.

        return round(first_correction, 2)


class Group:
    """A temporary implementation of the Group class, made only to enable those firepower correction rules which require
    knowing whether ships are adjacent.
    """
    def __init__(self, name, group_members, group_type, formation=True):
        self.name = name
        self.ships = group_members
        self.group_type = group_type
        self.formation = formation


class Side:
    """A temporary implementation of the Side class, made only to enable looking up a certain group for targeting."""
    def __init__(self, name, groups):
        self.name = name
        self.groups = groups


# TEST SHIPS (AUSTRALIA)

# Initialise the primary batteries.
sydney_primary = Battery(Gun("6-in-50"), "primary", "turret", 8, 2, 4, 2, 45, 1, False)
brisbane_primary = Battery(Gun("6-in-50"), "primary", "turret", 8, 2, 4, 2, 45, 1, False)
melbourne_primary = Battery(Gun("6-in-50"), "primary", "turret", 8, 2, 4, 2, 45, 1, False)

# Initialise the ships.
sydney = Ship("Sydney", "CL", "small", 3.17, 3, 2)
brisbane = Ship("Brisbane", "CL", "small", 3.17, 3, 2)
melbourne = Ship("Melbourne", "CL", "small", 3.17, 3, 2)

# Add the batteries.
sydney.add_gun_battery(sydney_primary)
brisbane.add_gun_battery(brisbane_primary)
melbourne.add_gun_battery(melbourne_primary)

# Add motion data.
sydney.initial_speed = brisbane.initial_speed = melbourne.initial_speed = 12
sydney.current_speed = brisbane.current_speed = melbourne.current_speed = 14
sydney.initial_course = brisbane.initial_course = melbourne.initial_course = 90
sydney.current_course = brisbane.current_course = melbourne.current_course = 120

# TEST SHIPS (GERMANY)

# Initialise the primary batteries.
emden_first = Battery(Gun("4-in-45-A"), "primary", "deck", 4, 2, 2, 2, 30, 1, False)
emden_second = Battery(Gun("4-in-45-A"), "primary", "broadside", 6, 2, 3, 2, 30, 1, False)
dresden_first = Battery(Gun("4-in-45-A"), "primary", "deck", 4, 2, 2, 2, 30, 1, False)
dresden_second = Battery(Gun("4-in-45-A"), "primary", "broadside", 6, 2, 3, 2, 30, 1, False)

# Initialise the ships.
emden = Ship("Emden", "CL", "small", 2.37, 3, 1.2)
dresden = Ship("Dresden", "CL", "small", 2.37, 3, 1.2)

# Add the batteries.
emden.add_gun_battery(emden_first)
emden.add_gun_battery(emden_second)
dresden.add_gun_battery(dresden_first)
dresden.add_gun_battery(dresden_second)

# Add motion data
emden.initial_speed = dresden.initial_speed = 10
emden.current_speed = dresden.current_speed = 15
emden.initial_course = dresden.initial_course = 80
emden.current_course = dresden.current_course = 90

# Test ship dictionary
ships = {"Sydney": sydney, "Melbourne": melbourne, "Brisbane": brisbane, "Emden": emden, "Dresden": dresden}

# Test group ship dictionaries
side_a_group_ships = {"Sydney": sydney, "Brisbane": brisbane, "Melbourne": melbourne}
side_b_group_ships = {"Emden": emden, "Dresden": dresden}

# Test groups
side_a_groups = {"Brisbane, Sydney and Melbourne": Group("Brisbane, Sydney and Melbourne", side_a_group_ships, False)}
side_b_groups = {"Emden and Dresden": Group("Emden and Dresden", side_b_group_ships, True)}

# Test sides
side_a = Side("Australia", side_a_groups)
side_b = Side("Germany", side_b_groups)

emden.target(ships, "Emden and Dresden", "Brisbane, Sydney and Melbourne", ["Brisbane"], True, "primary", 10, 90, False,
             45)

for battery in emden.primary_batteries:
    battery.allocate_mounts()

with pd.option_context('display.max_rows', 5, 'display.max_columns', None, 'display.width', None):
    print("Previous target data")
    print(emden.previous_target_data)
    print("")
    print("Current target data")
    print(emden.target_data)
    print("")
    for battery in emden.primary_batteries:
        print("Gun battery target data")
        print(battery.caliber)
        print(battery.target_data)
        print("")
