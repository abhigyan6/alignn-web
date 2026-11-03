"""Export the actual API contract; use npm run generate:api to update TypeScript too."""
import json
from pathlib import Path
from alignn.main import app
Path('packages/api-client/openapi.json').write_text(json.dumps(app.openapi(),indent=2,sort_keys=True)+'\n')
