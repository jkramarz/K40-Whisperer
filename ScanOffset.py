"""
    Scan Offset Calculator, Eli B

    No copyright included. To be used freely with K40 Whisperer. All copyrights apply as listed for
    K40 Whisperer.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""


class ScanOffset:
    def __init__(self, offsets=[[100, 0], [400, 0]], allowApproximation=True):
        """Create a new ScanOffset object.

        Args:
            offsets (list, list, optional): Create a table of offset lookups for speed settings. Defaults to [[100, 0] [400, 0]].
            allowApproximation (bool, optional): Allows offsets to be calculated for speeds not in the table using linear approximation. Defaults to True.
        """
        self.offsets = offsets
        self.allowApproximation = allowApproximation
        self.sortOffsets()

    def sortOffsets(self):
        """Sort the offsets by speed."""
        self.offsets.sort(key=lambda x: x[0])

    def canExactOffset(self, speed):
        """Check if an exact offset can be found for a given speed.

        Args:
            speed (int): The speed to check.

        Returns:
            bool: True if an exact offset can be found, False otherwise.
            offset (int): The offset for the given speed. (Only returned if True)
        """
        for offset in self.offsets:
            if speed == offset[0]:
                return True, offset[1]
        return False, None

    def getOffset(self, speed):
        """Get the offset for a given speed.

        Args:
            speed (int): The speed to get the offset for.

        Returns:
            int: The offset for the given speed.
        """
        exact, offset = self.canExactOffset(speed)
        if exact:
            return offset
        elif self.allowApproximation:
            return self.approximateOffset(speed)
        else:
            raise Exception("No offset found for speed " + str(speed) + ".")

    def approximateOffset(self, speed):
        """Approximate the offset for a given speed.

        Args:
            speed (int): The speed to approximate the offset for.

        Returns:
            int: The offset for the given speed.
        """
        for i in range(len(self.offsets)):
            if speed < self.offsets[i][0]:
                return self.offsets[i - 1][1] + (speed - self.offsets[i - 1][0]) * (
                    self.offsets[i][1] - self.offsets[i - 1][1]
                ) / (self.offsets[i][0] - self.offsets[i - 1][0])
        return self.offsets[-1][1] + (speed - self.offsets[-1][0]) * (
            self.offsets[-1][1] - self.offsets[-2][1]
        ) / (self.offsets[-1][0] - self.offsets[-2][0])

    def addOffset(self, speed, offset):
        """Add an offset to the table.

        Args:
            speed (int): The speed to add the offset for.
            offset (int): The offset to add.
        """
        self.offsets.append([speed, offset])
        self.sortOffsets()

    def removeOffset(self, speed):
        """Remove an offset from the table.

        Args:
            speed (int): The speed to remove the offset for.
        """
        for offset in self.offsets:
            if speed == offset[0]:
                self.offsets.remove(offset)
                return
        raise Exception("No offset found for speed " + str(speed) + ".")

    def setOffsets(self, offsets):
        """Set the offset table.

        Args:
            offsets (list): The new offset table.
        """
        self.offsets = offsets
        self.sortOffsets()

    def saveOffsets(self, path):
        """Save the offset table to a file.

        Args:
            path (str): The path to save the file to.
        """
        with open(path, "w") as f:
            for offset in self.offsets:
                f.write(str(offset[0]) + "," + str(offset[1]) + "\n")

    def loadOffsets(self, path):
        """Load the offset table from a file.

        Args:
            path (str): The path to load the file from.
        """
        with open(path, "r") as f:
            self.offsets = []
            for line in f:
                line = line.strip()
                if line == "":
                    continue
                offset = line.split(",")
                self.offsets.append([int(offset[0]), int(offset[1])])
            self.sortOffsets()
