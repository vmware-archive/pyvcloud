from packaging.version import Version


class VCDApiVersion(Version):
    """Objects representing VCD API versions.

    Pre-release versions also contain a pre-release segment.
    Example: '37.0.0-alpha-1625843840'.

    Need to override all the comparison functions because
    packaging.version.Version objects also compare pre-release segment
    for pre-release versions.
    """

    def __init__(self, version_string):
        super().__init__(version_string)

    def __eq__(self, vcd_api_version):
        if vcd_api_version.is_prerelease and self.is_prerelease and \
                vcd_api_version.pre[0] == self.pre[0] and \
                vcd_api_version.base_version == self.base_version:
            return True
        return super().__eq__(vcd_api_version)

    def __ne__(self, vcd_api_version):
        return not self.__eq__(vcd_api_version)

    def __lt__(self, vcd_api_version):
        if vcd_api_version.is_prerelease and self.is_prerelease and \
                vcd_api_version.pre[0] == self.pre[0] and \
                vcd_api_version.base_version == self.base_version:
            return False
        return super().__lt__(vcd_api_version)

    def __gt__(self, vcd_api_version):
        if vcd_api_version.is_prerelease and self.is_prerelease and \
                vcd_api_version.pre[0] == self.pre[0] and \
                vcd_api_version.base_version == self.base_version:
            return False
        return super().__gt__(vcd_api_version)

    def __lte__(self, vcd_api_version):
        return not self.__gt__(vcd_api_version)

    def __gte__(self, vcd_api_version):
        return not self.__lt__(vcd_api_version)
