from nose.tools import with_setup
from testconfig import config
from pyvcloud import vcloudair
from pyvcloud.score import Score, BlueprintsClient
from dsl_parser.exceptions import *


class TestScore:

    def __init__(self):
        self.vca = None
        self.score = Score('https://score.vca.io')

    def test_0001(self):
        """Validate blueprint"""
        blueprint_path = config['vcloud']['blueprint_path']
        blueprints_client = BlueprintsClient(self.score)
        try:
            plan = blueprints_client.validate(blueprint_path)
            assert plan
        except MissingRequiredInputError as mrie:
            raise Exception(str(mrie)[str(mrie).rfind('}') + 1:].strip())
        except UnknownInputError as uie:
            raise Exception(str(uie)[str(uie).rfind('}') + 1:].strip())
        except FunctionEvaluationError as fee:
            raise Exception(str(fee)[str(fee).rfind('}') + 1:].strip())
        except DSLParsingException as dpe:
            raise Exception(str(dpe)[str(dpe).rfind('}') + 1:].strip())
        except Exception as ex:
            raise Exception(
                'failed to validate %s:\n %s' %
                (blueprint_path, str(ex)))
