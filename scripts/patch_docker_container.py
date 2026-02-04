#!/usr/bin/env python3
"""
Patch Docker container to fix ColladaLoader registration error.

This script:
1. Finds the bundled JavaScript file in the Docker container
2. Creates a backup
3. Injects a runtime fix before the ColladaLoader registration code
4. Restarts the container if needed
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Windows encoding fix
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


def run_command(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout if hasattr(e, 'stdout') else '', e.stderr if hasattr(e, 'stderr') else ''


def find_js_file_in_container(container_name: str, pattern: str) -> str | None:
    """Find JavaScript file matching pattern in container."""
    cmd = [
        'docker', 'exec', container_name,
        'find', '/usr/share/nginx/html/assets',
        '-name', pattern,
        '-type', 'f'
    ]
    exit_code, stdout, stderr = run_command(cmd, check=False)
    
    if exit_code == 0 and stdout.strip():
        return stdout.strip().split('\n')[0]
    return None


def create_backup(container_name: str, file_path: str) -> str:
    """Create a backup of the file in the container."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    
    cmd = ['docker', 'exec', container_name, 'cp', file_path, backup_path]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        raise RuntimeError(f"Failed to create backup: {stderr}")
    
    print(f"[OK] Backup created: {backup_path}")
    return backup_path


def read_file_from_container(container_name: str, file_path: str) -> str:
    """Read file content from container."""
    # Use docker cp to copy file locally first (handles encoding better)
    temp_file = f"temp_{Path(file_path).name}"
    cmd = ['docker', 'cp', f"{container_name}:{file_path}", temp_file]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        raise RuntimeError(f"Failed to copy file: {stderr}")
    
    try:
        # Read with UTF-8 encoding and error handling
        with open(temp_file, encoding='utf-8', errors='replace') as f:
            content = f.read()
        return content
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def write_file_to_container(container_name: str, file_path: str, content: str) -> None:
    """Write file content to container."""
    # Write to temp file first
    temp_file = f"/tmp/{Path(file_path).name}"
    
    # Create temp file locally
    local_temp = Path(temp_file).name
    with open(local_temp, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        # Copy to container
        cmd = ['docker', 'cp', local_temp, f"{container_name}:{temp_file}"]
        exit_code, stdout, stderr = run_command(cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to copy temp file: {stderr}")
        
        # Move to final location
        cmd = ['docker', 'exec', container_name, 'mv', temp_file, file_path]
        exit_code, stdout, stderr = run_command(cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to move file: {stderr}")
        
        # Set permissions
        cmd = ['docker', 'exec', container_name, 'chmod', '644', file_path]
        run_command(cmd, check=False)
        
    finally:
        # Clean up local temp file
        if os.path.exists(local_temp):
            os.remove(local_temp)


def inject_fix(content: str) -> str:
    """Inject the runtime fix into the JavaScript content and replace problematic assignments."""
    import re
    
    # Read the fix script
    fix_script_path = Path(__file__).parent / 'fix-collada-loader.js'
    if not fix_script_path.exists():
        raise FileNotFoundError(f"Fix script not found: {fix_script_path}")
    
    with open(fix_script_path, encoding='utf-8') as f:
        fix_script = f.read()
    
    # First, inject the fix script at the beginning
    # Look for the start of the module/script
    if content.startswith('(function'):
        # Find the opening brace
        injection_index = content.find('{') + 1
    else:
        injection_index = 0
    
    # Inject the fix script first
    fix_marker_start = '// === INJECTED FIX FOR COLLADALOADER ==='
    fix_marker_end = '// === END INJECTED FIX ==='
    
    patched_content = (
        content[:injection_index] +
        f'\n\n{fix_marker_start}\n' +
        fix_script +
        f'\n{fix_marker_end}\n\n' +
        content[injection_index:]
    )
    
    # Find where the fix script ends (so we don't replace code inside it)
    fix_end_index = patched_content.find(fix_marker_end) + len(fix_marker_end)
    
    # Split content: fix script (don't touch) + bundle code (replace)
    fix_script_section = patched_content[:fix_end_index]
    bundle_code_section = patched_content[fix_end_index:]
    
    # Now find and replace problematic assignments ONLY in bundle code
    # Pattern: THREE.Loader.ColladaLoader = something;
    # Replace with safe registration that ALWAYS uses try-catch
    pattern = r'THREE\.Loader\.ColladaLoader\s*=\s*([^;]+);'
    
    # Safe replacement that ALWAYS uses fix function, never direct assignment
    replacement = r'''try {
        if (typeof window !== 'undefined' && window.__THREE_LOADER_FIX__) {
            window.__THREE_LOADER_FIX__(\1);
        } else {
            // Fallback: use alternative namespace (never assign to THREE.Loader.ColladaLoader)
            THREE.ColladaLoader = \1;
            console.warn('ColladaLoader registered to THREE.ColladaLoader (fix function not available)');
        }
    } catch (e) {
        console.warn('ColladaLoader registration failed:', e);
        try {
            THREE.ColladaLoader = \1;
        } catch (e2) {
            console.error('Failed to register ColladaLoader:', e2);
        }
    }'''
    
    # Only replace in bundle code section
    patched_bundle = re.sub(pattern, replacement, bundle_code_section)
    
    # Combine back
    patched_content = fix_script_section + patched_bundle
    
    return patched_content


def patch_proxy_set_trap(content: str) -> str:
    """Patch the Proxy get and set traps in the main bundle to handle non-extensible objects."""
    import re
    
    # Pattern 1: get(n,r){return n[r]}
    # Replace with get that wraps Loader in a Proxy
    get_pattern = r'get\(n,r\)\{return n\[r\]\}'
    get_replacement = r'''get(n,r){
        const value = n[r];
        // If getting Loader, wrap it in a Proxy that allows ColladaLoader
        // Handle both function and object types (THREE.Loader can be either)
        if (r === 'Loader' && value && (typeof value === 'object' || typeof value === 'function')) {
            // Use WeakMap to store proxies to avoid memory leaks and re-wrapping
            if (!window.__THREE_LOADER_PROXIES__) {
                window.__THREE_LOADER_PROXIES__ = new WeakMap();
            }
            let loaderProxy = window.__THREE_LOADER_PROXIES__.get(value);
            if (loaderProxy) return loaderProxy;
            
            // Use WeakMap to store fallback values (works even if target is not extensible)
            if (!window.__THREE_LOADER_FALLBACKS__) {
                window.__THREE_LOADER_FALLBACKS__ = new WeakMap();
            }
            
            // Create a Proxy that allows setting ColladaLoader
            loaderProxy = new Proxy(value, {
                get(target, prop) {
                    // Check fallback map first
                    const fallbacks = window.__THREE_LOADER_FALLBACKS__.get(target);
                    if (fallbacks && fallbacks.hasOwnProperty(prop)) {
                        return fallbacks[prop];
                    }
                    return target[prop];
                },
                set(target, prop, val) {
                    // Always return true - never throw errors
                    // Use Reflect.set which returns boolean instead of throwing
                    if (Object.isExtensible(target)) {
                        const success = Reflect.set(target, prop, val);
                        if (success) return !0;
                    }
                    // Try defineProperty
                    try {
                        const success = Reflect.defineProperty(target, prop, {
                            value: val,
                            writable: true,
                            enumerable: true,
                            configurable: true
                        });
                        if (success) return !0;
                    } catch (e) {
                        // defineProperty failed, continue to fallback
                    }
                    // Last resort: store in WeakMap fallback
                    try {
                        let fallbacks = window.__THREE_LOADER_FALLBACKS__.get(target);
                        if (!fallbacks) {
                            fallbacks = {};
                            window.__THREE_LOADER_FALLBACKS__.set(target, fallbacks);
                        }
                        fallbacks[prop] = val;
                        // Also set on THREE.ColladaLoader as fallback
                        if (prop === 'ColladaLoader' && typeof window !== 'undefined' && window.THREE) {
                            try {
                                window.THREE.ColladaLoader = val;
                            } catch (e) {
                                // Ignore
                            }
                        }
                    } catch (e) {
                        // Ignore all errors
                    }
                    return !0;
                }
            });
            // Cache the proxy
            window.__THREE_LOADER_PROXIES__.set(value, loaderProxy);
            return loaderProxy;
        }
        return value;
    }'''
    
    # Pattern 2: set(n,r,i){return n[r]=i,!0}
    # Replace with safe set that handles non-extensible objects
    set_pattern = r'set\(n,r,i\)\{return n\[r\]=i,!0\}'
    set_replacement = r'''set(n,r,i){
        // Use Reflect.set which returns boolean instead of throwing
        if (Object.isExtensible(n)) {
            const success = Reflect.set(n, r, i);
            if (success) return !0;
        }
        // Try defineProperty
        try {
            const success = Reflect.defineProperty(n, r, {
                value: i,
                writable: true,
                enumerable: true,
                configurable: true
            });
            if (success) return !0;
        } catch (e) {
            // defineProperty failed, continue
        }
        // Always return true to prevent errors
        return !0;
    }'''
    
    patched_content = re.sub(get_pattern, get_replacement, content)
    patched_content = re.sub(set_pattern, set_replacement, patched_content)
    return patched_content


def patch_container(container_name: str = 'ai-automation-ui') -> None:
    """Main patching function."""
    print(f"[PATCH] Patching container: {container_name}")
    
    # Find both bundles: react-force-graph and main index bundle
    print("[SEARCH] Searching for JavaScript bundles...")
    react_force_graph_file = find_js_file_in_container(container_name, '*react-force-graph*.js')
    index_file = find_js_file_in_container(container_name, '*index*.js')
    
    files_to_patch = []
    if react_force_graph_file:
        files_to_patch.append(('react-force-graph', react_force_graph_file))
    if index_file:
        files_to_patch.append(('index', index_file))
    
    if not files_to_patch:
        print("[WARN] Could not find JavaScript bundles")
        raise FileNotFoundError("Could not find JavaScript bundles in container")
    
    print(f"[OK] Found {len(files_to_patch)} file(s) to patch")
    
    for file_type, js_file in files_to_patch:
        print(f"\n[PATCH] Patching {file_type} bundle: {js_file}")
        
        # Create backup
        print("[BACKUP] Creating backup...")
        create_backup(container_name, js_file)
        
        # Read current content
        print("[READ] Reading file content...")
        content = read_file_from_container(container_name, js_file)
        print(f"       File size: {len(content)} bytes")
        
        # Check if already patched
        if 'INJECTED FIX FOR COLLADALOADER' in content or '// PATCHED PROXY SET TRAP' in content:
            print("[WARN] File appears to already be patched")
            if '--force' not in sys.argv:
                print("       Use --force flag to re-patch, or the fix is already applied.")
                continue
            print("       Re-patching with --force flag...")
        
        # Inject fix based on file type
        print("[INJECT] Injecting fix...")
        if file_type == 'index':
            # Patch the Proxy set trap in the main bundle
            patched_content = patch_proxy_set_trap(content)
            # Also inject the fix script at the beginning
            fix_script_path = Path(__file__).parent / 'fix-collada-loader.js'
            if fix_script_path.exists():
                with open(fix_script_path, encoding='utf-8') as f:
                    fix_script = f.read()
                patched_content = (
                    '// PATCHED PROXY SET TRAP\n' +
                    fix_script + '\n' +
                    patched_content
                )
        else:
            # Patch react-force-graph bundle
            patched_content = inject_fix(content)
        
        print(f"        New file size: {len(patched_content)} bytes")
        print(f"        Added: {len(patched_content) - len(content)} bytes")
        
        # Write patched content
        print("[WRITE] Writing patched file...")
        write_file_to_container(container_name, js_file, patched_content)
        print(f"[OK] {file_type} bundle patched successfully")
    
    # Restart container (optional)
    auto_restart = '--no-restart' not in sys.argv
    
    if auto_restart:
        print("\n[RESTART] Restarting container...")
        cmd = ['docker', 'restart', container_name]
        exit_code, stdout, stderr = run_command(cmd)
        if exit_code == 0:
            print("[OK] Container restarted")
        else:
            print(f"[WARN] Restart failed: {stderr}")
            print("       You may need to restart manually: docker restart ai-automation-ui")
    else:
        print("\n[SKIP] Skipping container restart (use --no-restart flag)")
        print("       Restart manually: docker restart ai-automation-ui")
    
    print("\n[SUCCESS] Patching complete!")
    print("         Test the fix at: http://localhost:3001/synergies")


if __name__ == '__main__':
    container_name = sys.argv[1] if len(sys.argv) > 1 else 'ai-automation-ui'
    
    try:
        patch_container(container_name)
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
