#!/usr/bin/env python3
"""
Simplified compilation script for the alpha-beta pruning C++ module.
This script uses a more direct approach to compile the module on macOS.
"""
import os
import sys
import subprocess
import platform
import sysconfig
import shlex

def main():
    print("Compiling alpha-beta pruning C++ module...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source file
    cpp_file = os.path.join(script_dir, "alpha-beta-pruning.cpp")
    
    # Output library name
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = ".so"
    
    output_file = os.path.join(script_dir, f"hex_cpp{ext_suffix}")
    
    # Get Python includes and library paths
    python_include = sysconfig.get_path('include')
    python_executable = sys.executable
    
    # Use Python3-config to get compiler and linker flags
    try:
        config_cmd = os.path.join(os.path.dirname(python_executable), 'python3-config')
        if not os.path.exists(config_cmd):
            config_cmd = 'python3-config'
        
        cflags = subprocess.check_output([config_cmd, '--cflags']).decode().strip()
        ldflags = subprocess.check_output([config_cmd, '--ldflags']).decode().strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Warning: Could not get flags from python3-config, using defaults")
        cflags = f"-I{python_include}"
        if platform.system() == 'Darwin':
            ldflags = "-undefined dynamic_lookup"
        else:
            ldflags = ""
    
    # Add pybind11 include
    try:
        import pybind11
        pybind_include = pybind11.get_include()
        cflags += f" -I{pybind_include}"
    except ImportError:
        print("ERROR: pybind11 is required but not installed.")
        print("Please install it using: pip install pybind11")
        sys.exit(1)
    
    # Compiler based on platform
    if platform.system() == 'Darwin':  # macOS
        compiler = "clang++"
        compile_flags = f"{cflags} -std=c++17 -O3 -shared -fPIC -undefined dynamic_lookup"
    elif platform.system() == 'Linux':
        compiler = "g++"
        compile_flags = f"{cflags} -std=c++17 -O3 -shared -fPIC"
    else:  # Windows
        compiler = "cl"
        compile_flags = "/EHsc /Ox /std:c++17"

    # Use subprocess.run with a list of args to avoid shell escaping issues
    cmd_parts = []
    
    cmd_parts.append(compiler)
    cmd_parts.extend(compile_flags.split())
    
    # When on non-Windows, add ldflags
    if platform.system() != 'Windows':
        cmd_parts.extend(ldflags.split())
    
    # Add input file
    cmd_parts.append(cpp_file)
    
    # Add output directive
    if platform.system() == 'Windows':
        cmd_parts.extend(["/link", ldflags, f"/out:{output_file}"])
    else:
        cmd_parts.extend(["-o", output_file])
    
    print(f"Running: {' '.join(shlex.quote(part) for part in cmd_parts)}")
    
    # Execute the command
    try:
        subprocess.run(cmd_parts, check=True)
        print(f"Successfully compiled C++ module to {output_file}")
        
        # Copy the module to the parent directory for easier importing
        parent_dir = os.path.dirname(script_dir)
        parent_output = os.path.join(parent_dir, os.path.basename(output_file))
        import shutil
        shutil.copy2(output_file, parent_output)
        print(f"Copied module to {parent_output}")
        
        # Create a symlink with the name alpha_beta_pruning.so for backward compatibility
        alpha_beta_link = os.path.join(parent_dir, "alpha_beta_pruning.so")
        if os.path.exists(alpha_beta_link):
            os.unlink(alpha_beta_link)
        
        if platform.system() != 'Windows':
            try:
                os.symlink(os.path.basename(parent_output), alpha_beta_link)
                print(f"Created symlink {alpha_beta_link} -> {os.path.basename(parent_output)}")
            except OSError:
                # Fall back to copying if symlink fails
                shutil.copy2(parent_output, alpha_beta_link)
                print(f"Created copy {alpha_beta_link}")
        else:
            # Windows needs special permissions for symlinks, so just copy
            shutil.copy2(parent_output, alpha_beta_link)
            print(f"Created copy {alpha_beta_link}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error compiling C++ module: {e}")
        return False

if __name__ == "__main__":
    main()