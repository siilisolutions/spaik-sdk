"""Pack public packages and build a fresh app using tarballs, without workspace links."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dist", default="release-dist")
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
dist = Path(args.dist).resolve()
dist.mkdir(parents=True, exist_ok=True)
artifacts = []
for package in ["agent-sdk-hooks", "agent-sdk-material"]:
    output = subprocess.check_output(
        ["npm", "pack", "--json", "--pack-destination", str(dist)],
        cwd=root / "packages" / package,
        text=True,
    )
    artifacts.append(str(dist / json.loads(output)[0]["filename"]))

with tempfile.TemporaryDirectory(prefix="spaik-installed-ui-") as directory:
    app = Path(directory).resolve()
    (app / "package.json").write_text(json.dumps({"name": "spaik-installed-check", "private": True, "type": "module"}))
    subprocess.run(
        ["npm", "install", "--no-audit", "--no-fund", *artifacts, "react@18", "react-dom@18", "vite@6", "typescript@5", "@types/react@18", "@types/react-dom@18"],
        cwd=app,
        check=True,
    )
    (app / "index.html").write_text('<div id="root"></div><script type="module" src="/main.tsx"></script>')
    (app / "main.tsx").write_text('''import React from 'react';
import { createRoot } from 'react-dom/client';
import { HttpAgent } from 'spaik-sdk-react';
import { AgentChat } from 'spaik-sdk-material';
const agent = new HttpAgent({ url: 'http://localhost:8000/agent' });
createRoot(document.getElementById('root')!).render(<AgentChat agent={agent} />);
''')
    (app / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler", "jsx": "react-jsx", "strict": True, "noEmit": True, "skipLibCheck": True}, "include": ["main.tsx"]}))
    for command in ["tsc", "vite"]:
        subprocess.run([str(app / "node_modules" / ".bin" / command), *(["build"] if command == "vite" else [])], cwd=app, check=True)
print("Installed npm artifacts: type check and production build passed")
