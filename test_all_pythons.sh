#!/bin/bash
# Test package builds on all Python versions

echo "Testing package builds across Python versions..."
echo ""

for py in 3.8 3.9 3.10 3.11; do
    echo "=== Python $py ==="
    
    # Create venv
    rm -rf .test-venv-$py
    uv venv --python $py .test-venv-$py 2>&1 | grep -E "(Using|Creating)" || true
    
    # Build package
    source .test-venv-$py/bin/activate
    uv pip install build > /dev/null 2>&1
    rm -rf build dist
    rm -rf *.egg-info 2>/dev/null || true
    python -m build > /dev/null 2>&1
    
    if [ $? -eq 0 ] && [ -f dist/*.whl ]; then
        echo "  ✓ Build successful"
        # Test install
        uv pip install dist/*.whl > /dev/null 2>&1
        python -c "from tentoku import tokenize, SQLiteDictionary; print('  ✓ Import successful')" 2>&1
    else
        echo "  ✗ Build failed"
    fi
    
    deactivate 2>/dev/null
    echo ""
done

# Cleanup
rm -rf .test-venv-*
