# Hex Game

A Python implementation of the Hex board game with AI using alpha-beta pruning and a C++ backend for performance.

## Running the Game

Due to setuptools conflicts in the Python environment, the game cannot be run directly with `python3 frontend/front.py`. Instead, use one of the following launchers:

### Recommended: Use the isolated launcher

```bash
./run_hex_isolated.sh
```

This launcher creates a completely isolated Python environment to run the game, bypassing any system-level Python configuration that might be causing conflicts.

### Alternative: AppleScript launcher

```bash
./launch_hex.sh
```

This will open a new Terminal window and launch the game.

### The setuptools conflict issue

If you attempt to run the game directly, you may encounter this error:

```
usage: front.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
   or: front.py --help [cmd1 cmd2 ...]
   or: front.py --help-commands
   or: front.py cmd --help
error: no commands supplied
```

This happens because the Python environment has a deep integration with setuptools that's intercepting the script execution. The launcher scripts work around this issue using different approaches.

## C++ Extension

The game uses a C++ extension compiled with pybind11 for the alpha-beta pruning algorithm. The extension has been successfully compiled for macOS with Apple Silicon (arm64) architecture.

## Game Features

- Standard Hex game rules with blue and red players
- Three AI difficulty levels 
- Player vs Player, Player vs AI, and AI vs AI modes
- Move history navigation
- Swap rule implementation
