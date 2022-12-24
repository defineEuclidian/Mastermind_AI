from mastermind import *

class LMU(Player):
    def __init__(self):
        self.player_name = "LMU Advanced Pairwise Deduction"
        
        self.color_total = 0 # Total number of colors counted so far

        self.pattern = [] # A list that contains the current guess pattern/code

        # A list of dictionaries that contains information about a color at some position for all possible colors in positions 0 to board_length - 1; each color is associated with a 0, 1, or 2
        # 0 = unknown; the color at this particular position either does not belong to this position or it does belong to this position
        # 1 = the color at this particular position does not belong to this position
        # 2 = the color at this particular position does belong to this position
        self.position_info = []

        self.colors_left = {} # A dictionary that contains, for each color, how many colors are currently unaccounted for

        self.first = 0 # One of two indices for a color to be swapped with another
        self.second = 0 # One of two indices for a color to be swapped with another

        self.last_count = 0 # Previous number of pins from the previous self.pattern permutation
        self.last_saved = None # Used to store an overwritten color for later restoration
        
        self.evaluate = False # Boolean to trigger a sub-routine for +1 or -1 cases
        self.evaluate_possible_duplicate = False # Boolean to trigger a sub-routine for a possible duplicate in a +0 case
        self.evaluate_duplicate_found = False # Boolean to trigger a sub-routine for a confirmed duplicate

        self.begin = False # Boolean to insure that pair-switching can occur in the event of an early stopping of checking all colors
        self.skip_colors = False # Boolean to insure that we can stop checking all colors early

        self.anneal_factor = 0 # For slowly decreasing the current acceptable amount of initial correct positions
        self.anneal_shifted = False # Boolean to trigger our best-case initial positions heuristic

    def make_guess(
        self,
        board_length: int,
        colors: list[str],
        scsa_name: str,
        last_response: tuple[int, int, int],
        ) -> str:

        color_pos_pins = last_response[0]
        guess = last_response[2]
        
        diff_curr_last = color_pos_pins - self.last_count

        pttrn = self.pattern
        info = self.position_info
        lcolors = self.colors_left

        # Start off with all-color guesses until the total number of colors found is equal to board_length
        # self.pattern and self.colors_left are updated as these guesses are made
        # Then, shuffle self.pattern and begin pair-switching
        
        if guess == 0:
            self.__init__()
            
            allcolorguess = ""
            
            for i in range(board_length):
                allcolorguess += colors[0]

            return allcolorguess
        
        elif guess < len(colors) - 1 and not self.skip_colors:
            if color_pos_pins != 0:
                self.color_total += color_pos_pins
                lcolors[colors[guess - 1]] = color_pos_pins
                for i in range(color_pos_pins):
                    pttrn.append(colors[guess - 1])

            if self.color_total == board_length:
                self.skip_colors = True
                random.shuffle(pttrn)
                return list_to_str(pttrn)

            allcolorguess = ""
            
            for i in range(board_length):
                allcolorguess += colors[guess]
            
            return allcolorguess
            
        elif guess == len(colors) - 1 and not self.skip_colors:
            if color_pos_pins != 0:
                self.color_total += color_pos_pins
                lcolors[colors[guess - 1]] = color_pos_pins
                for i in range(color_pos_pins):
                    pttrn.append(colors[guess - 1])

            if self.color_total < board_length:
                lcolors[colors[guess]] = board_length - self.color_total
                for i in range(board_length - self.color_total):
                    pttrn.append(colors[guess])
            
            random.shuffle(pttrn)

            return list_to_str(pttrn)

        elif (guess == len(colors) or self.skip_colors) and not self.begin:
            self.last_count = color_pos_pins
            self.begin = True

            for i in range(board_length):
                info.append({})
                for k in lcolors:
                    info[i][k] = 0

            if color_pos_pins == 0:
                for i in range(board_length):
                    info[i][pttrn[i]] = 1
            
            if color_pos_pins <= board_length // len(colors):
                for i in range(board_length - 1):
                    temp = pttrn[i]
                    pttrn[i] = pttrn[i + 1]
                    pttrn[i + 1] = temp
                
                self.anneal_shifted = True
            else:
                either_invalid = True

                while pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                    self.second += 1
                    self.second %= board_length
                    if self.second == 0:
                        self.first += 1
                        self.first %= board_length
                        if self.first == 0:
                            either_invalid = False
                
                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

            return list_to_str(pttrn)

        # At any point the number of pins equals 0, all colors in their current positions are invalid

        if color_pos_pins == 0:
            for i in range(board_length):
                info[i][pttrn[i]] = 1
        
        # A heuristic sub-routine for when the amount of initial correct positions in self.pattern is less than or equal to the average amount of initial correct positions
        # Simply shift the pattern to the left until we have a greater than average amount of initial correct positions
        # However, this acceptable value we are comparing color_pos_pins to is decreased over time to avoid too many unnecessary guesses

        # Inspired by Simulated Annealing, but in this case the amount of shifts decrease as the "temperature" increases

        if self.anneal_shifted:
            self.last_count = color_pos_pins
            
            if color_pos_pins <= (board_length // len(colors)) - (self.anneal_factor // 2):
                self.anneal_factor += 1

                for i in range(board_length - 1):
                    temp = pttrn[i]
                    pttrn[i] = pttrn[i + 1]
                    pttrn[i + 1] = temp
            else:
                either_invalid = True

                while pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                    self.second += 1
                    self.second %= board_length
                    if self.second == 0:
                        self.first += 1
                        self.first %= board_length
                        if self.first == 0:
                            either_invalid = False

                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

                self.anneal_shifted = False

            return list_to_str(pttrn)

        # A sub-routine for the non-duplicate color that was found from a +0 evaluation case
        # For this routine, -1, +1, and +0 have different meanings
        # -1 = When the non-duplicate color was inserted, the duplicate color that was previously there was actually in the correct position
        # +1 = When the non-duplicate color was inserted, the non-duplicate color is now in a correct position
        # +0 = When the non-duplicate color was inserted, the non-duplicate color is now in a position it does not belong to, and the duplicate color that was previously there also does not belong to that position

        if self.evaluate_duplicate_found:
            if diff_curr_last == 1 or diff_curr_last == 0:
                if diff_curr_last == 1:
                    self.last_count = color_pos_pins
                    info[self.second][pttrn[self.second]] = 2
                    lcolors[pttrn[self.second]] -= 1
                else:
                    info[self.second][pttrn[self.second]] = 1
                    info[self.second][self.last_saved] = 1
                    self.first = self.second

                while info[self.first][pttrn[self.first]] == 2:
                    self.first += 1
                    self.first %= board_length
                
                old_first = self.first
                old_second = self.second
                either_invalid = True

                while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                    self.second += 1
                    self.second %= board_length
                    if self.second == old_second:
                        self.first += 1
                        self.first %= board_length
                        while info[self.first][pttrn[self.first]] == 2:
                            self.first += 1
                            self.first %= board_length
                        if self.first == old_first:
                            either_invalid = False
                
                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

                self.evaluate_duplicate_found = False
            
            else:
                temp = pttrn[self.second]
                pttrn[self.second] = self.last_saved

                info[self.second][pttrn[self.second]] = 2
                lcolors[pttrn[self.second]] -= 1

                while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] != self.last_saved:
                    self.second += 1
                    self.second %= board_length

                pttrn[self.second] = temp

            return list_to_str(pttrn)

        # This possible duplicate evaluation sub-routine will use an extra guess to determine if a color is duplicated at self.first and self.second
        # The color saved from being overwritten by the duplicate color is then placed at some possibly incorrect position containing the duplicated color

        if self.evaluate_possible_duplicate:
            pttrn[self.second] = self.last_saved

            if diff_curr_last == 1 or diff_curr_last == -1:
                self.last_count += 1

                temp = None
                    
                if diff_curr_last == 1:
                    temp = pttrn[self.second]
                    pttrn[self.second] = pttrn[self.first]
                    self.last_saved = pttrn[self.first]
                else:
                    temp = pttrn[self.first]
                    pttrn[self.first] = pttrn[self.second]
                    self.last_saved = pttrn[self.second]

                info[self.first][pttrn[self.first]] = 2
                info[self.second][pttrn[self.second]] = 2
                lcolors[pttrn[self.first]] -= 1
                lcolors[pttrn[self.second]] -= 1

                while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] != pttrn[self.first]:
                    self.second += 1
                    self.second %= board_length

                pttrn[self.second] = temp

                self.evaluate_duplicate_found = True

            else:
                info[self.first][pttrn[self.first]] = 1
                info[self.first][pttrn[self.second]] = 1
                info[self.second][pttrn[self.first]] = 1
                info[self.second][pttrn[self.second]] = 1

                old_first = self.first
                old_second = self.second
                either_invalid = True

                while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                    self.second += 1
                    self.second %= board_length
                    if self.second == old_second:
                        self.first += 1
                        self.first %= board_length
                        while info[self.first][pttrn[self.first]] == 2:
                            self.first += 1
                            self.first %= board_length
                        if self.first == old_first:
                            either_invalid = False

                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

            self.evaluate_possible_duplicate = False

            return list_to_str(pttrn)

        # This evaluation sub-routine will use an extra guess to determine if a color at self.first or self.second is in the correct position

        if self.evaluate:
            pttrn[self.second] = self.last_saved
            
            if diff_curr_last == 0:
                info[self.first][pttrn[self.first]] = 2
                lcolors[pttrn[self.first]] -= 1
                info[self.second][pttrn[self.first]] = 1
                info[self.second][pttrn[self.second]] = 1
                self.first = self.second
            else:
                info[self.second][pttrn[self.second]] = 2
                lcolors[pttrn[self.second]] -= 1
                info[self.first][pttrn[self.first]] = 1
                info[self.first][pttrn[self.second]] = 1

            old_first = self.first
            old_second = self.second
            either_invalid = True

            while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                self.second += 1
                self.second %= board_length
                if self.second == old_second:
                    self.first += 1
                    self.first %= board_length
                    while info[self.first][pttrn[self.first]] == 2:
                        self.first += 1
                        self.first %= board_length
                    if self.first == old_first:
                        either_invalid = False

            temp = pttrn[self.first]
            pttrn[self.first] = pttrn[self.second]
            pttrn[self.second] = temp

            self.evaluate = False

            return list_to_str(pttrn)

        # Case where a pair switch resulted in a +1, -1, or +0 change in correct positions; requires an extra guess (self.evaluate) to see which colors are actually in a correct position
        # +1 = either color in their new positions is in a correct position
        # -1 = either color in their old positions was in a correct position
        # +0 = either color is duplicated in both positions, or neither color belongs in their new/old positions

        if diff_curr_last == 1 or diff_curr_last == -1 or diff_curr_last == 0:
            if diff_curr_last != 0 or lcolors[pttrn[self.first]] > 1 or lcolors[pttrn[self.second]] > 1:
                self.evaluate = diff_curr_last != 0
                self.evaluate_possible_duplicate = diff_curr_last == 0

                if diff_curr_last == 1:
                    self.last_count = color_pos_pins
                else:
                    temp = pttrn[self.first]
                    pttrn[self.first] = pttrn[self.second]
                    pttrn[self.second] = temp

                self.last_saved = pttrn[self.second]
                pttrn[self.second] = pttrn[self.first]

            else:
                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

                info[self.first][pttrn[self.first]] = 1
                info[self.first][pttrn[self.second]] = 1
                info[self.second][pttrn[self.first]] = 1
                info[self.second][pttrn[self.second]] = 1

                old_first = self.first
                old_second = self.second
                either_invalid = True

                while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                    self.second += 1
                    self.second %= board_length
                    if self.second == old_second:
                        self.first += 1
                        self.first %= board_length
                        while info[self.first][pttrn[self.first]] == 2:
                            self.first += 1
                            self.first %= board_length
                        if self.first == old_first:
                            either_invalid = False

                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

            return list_to_str(pttrn)

        # Case where a pair switch resulted in a +2 or -2 change in correct positions; no extra guess (self.evaluate) is required
        # +2 = Both colors in their new positions are now in correct positions
        # -2 = Both colors in their old positions were in correct positions

        elif diff_curr_last == 2 or diff_curr_last == -2:
            if diff_curr_last == 2:
                self.last_count = color_pos_pins
            else:
                temp = pttrn[self.first]
                pttrn[self.first] = pttrn[self.second]
                pttrn[self.second] = temp

            info[self.first][pttrn[self.first]] = 2
            info[self.second][pttrn[self.second]] = 2
            lcolors[pttrn[self.first]] -= 1
            lcolors[pttrn[self.second]] -= 1

            while info[self.first][pttrn[self.first]] == 2:
                self.first += 1
                self.first %= board_length
            
            old_first = self.first
            old_second = self.second
            either_invalid = True

            while info[self.second][pttrn[self.second]] == 2 or pttrn[self.second] == pttrn[self.first] or info[self.first][pttrn[self.second]] == 1 or info[self.second][pttrn[self.first]] == 1 and either_invalid:
                self.second += 1
                self.second %= board_length
                if self.second == old_second:
                    self.first += 1
                    self.first %= board_length
                    while info[self.first][pttrn[self.first]] == 2:
                        self.first += 1
                        self.first %= board_length
                    if self.first == old_first:
                        either_invalid = False
            
            temp = pttrn[self.first]
            pttrn[self.first] = pttrn[self.second]
            pttrn[self.second] = temp

            return list_to_str(pttrn)
