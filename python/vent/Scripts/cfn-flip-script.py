#!"D:\4 - Works\GitHub\xlight\Alexa\lambda-xlightdemo\python\vent\Scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'cfn-flip==1.0.0','console_scripts','cfn-flip'
__requires__ = 'cfn-flip==1.0.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('cfn-flip==1.0.0', 'console_scripts', 'cfn-flip')()
    )
