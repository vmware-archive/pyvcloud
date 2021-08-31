from packaging.version import Version


class VCDApiVersion(Version):
    def __init__(self, version_string):
        super().__init__(version_string)

    def __eq__(self, vcd_api_version):
        if vcd_api_version.is_prerelease and self.is_prerelease and \
                vcd_api_version.pre[0] == self.pre[0] and \
                vcd_api_version.base_version == self.base_version:
            return True
        return super().__eq__(vcd_api_version)

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
