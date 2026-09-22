"""Small dependency-free preflight check; use openapi-spec-validator in CI too."""
import sys
import yaml

if len(sys.argv) < 2:
    print("Usage: python3 validate_openapi.py <spec.yaml>")
    sys.exit(1)

with open(sys.argv[1]) as stream:
    document = yaml.safe_load(stream)

errors = []
if document.get("openapi") != "3.0.3":
    errors.append("Expected OpenAPI 3.0.3")
if not document.get("info") or not document.get("servers"):
    errors.append("info and servers are required")

for path, methods in document.get("paths", {}).items():
    for verb, operation in methods.items():
        if verb.lower() not in {"get", "post", "put", "patch", "delete", "options"}:
            continue
        if verb.lower() != "options" and not (operation.get("parameters") or operation.get("requestBody")):
            errors.append(f"{verb} {path}: no inputs declared")
        if len(operation.get("responses", {})) < 1:
            errors.append(f"{verb} {path}: fewer than one response")

if errors:
    print("OpenAPI preflight errors:\n- " + "\n- ".join(errors))
    raise SystemExit(1)

print("OpenAPI document parsed successfully.\nStructural checks completed: 0 errors.")
