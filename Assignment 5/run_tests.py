"""Standalone test runner requiring zero external dependencies."""
import sys
import time
from pathlib import Path

# Add tests directory
sys.path.insert(0, str(Path(__file__).parent / "tests"))
import test_orders

test_funcs = [
    getattr(test_orders, name)
    for name in sorted(dir(test_orders))
    if name.startswith("test_") and callable(getattr(test_orders, name))
]

print(f"Running {len(test_funcs)} test cases for CampusEats Orders API (Assignment 5)...")
passed = 0
failed = 0
start_time = time.time()

for func in test_funcs:
    name = func.__name__
    try:
        func()
        print(f"  [PASS] {name}")
        passed += 1
    except AssertionError as err:
        print(f"  [FAIL] {name}: Assertion Error ({err})")
        failed += 1
    except Exception as exc:
        print(f"  [ERROR] {name}: {type(exc).__name__}: {exc}")
        failed += 1

elapsed = time.time() - start_time
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed in {elapsed:.3f}s")
print("=" * 60)

if failed > 0:
    sys.exit(1)
