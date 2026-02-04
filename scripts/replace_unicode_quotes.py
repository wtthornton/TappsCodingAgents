# Fix create_github_release.ps1: corrupt line and smart quotes
import os
import re

path = os.path.join(os.path.dirname(__file__), 'create_github_release.ps1')
with open(path, encoding='utf-8', errors='replace') as f:
    c = f.read()
# Fix corrupted "  ... Version verified: $Version" line (e.g. [OK] or quote damage)
c = re.sub(r'    Write-Host "  .*? Version verified: \$Version" -ForegroundColor Green',
           r"    Write-Host ('  [OK] Version verified: {0}' -f $Version) -ForegroundColor Green", c)
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('Fixed create_github_release.ps1')
