from abc import ABC
from abc import abstractstaticmethod
import os
import re

from pyvcloud.vcd.exceptions import InvalidParameterException


class Validator(ABC):
    def validate(self, input=None):
        pass


class ValidateFolderExistence(Validator):
    def validate(self, input=None):
        """Check given directory for existence.

        :return input
        """
        if os.path.exists(input):
            return input

        return None


class LengthValidator(Validator):
    def __init__(self, minL=0, maxL=0):
        if minL < 0 or maxL < 0:
            raise InvalidParameterException(
                """Minimum bound can't be less then 0."""
            )

        if minL > maxL:
            raise InvalidParameterException(
                """Minimum bound can be greather
                then the maximum bound."""
            )

        self.minL = minL
        self.maxL = maxL

    def validate(self, input=None):
        """Check input length.

        :param integer minL
        :param integer maxL

        :return input
        """
        if len(input) >= self.minL and len(input) <= self.maxL:
            return input

        return None


class PatternValidator(Validator):
    def __init__(self, pattern):
        self.pattern = pattern

    def validate(self, input=None):
        """Check input structure agains given pattern.

        :return input
        """
        if re.match(self.pattern, input):
            return input

        return None


class ValidatorFactory(ABC):
    @abstractstaticmethod
    def checkForFolderExistence():
        return ValidateFolderExistence()

    @abstractstaticmethod
    def pattern(pattern):
        return PatternValidator(pattern)

    @abstractstaticmethod
    def length(minL, maxL):
        return LengthValidator(minL=minL, maxL=maxL)
