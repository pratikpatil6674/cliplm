"""Backward-compatible shim for the refactored Linux setup verifier package.

The project previously imported from a single-file module named `LinuxSetupVerifier`.
To keep those imports stable while moving to a more maintainable package layout,
this module simply re-exports the public entrypoints from `linux_setup_verifier`.
"""

from linux_setup_verifier import LinuxSetupVerifier, show_qt_dialog_from_payload, verify_linux_system_setup

__all__ = [
    "LinuxSetupVerifier",
    "verify_linux_system_setup",
    "show_qt_dialog_from_payload",
]
