# Launch and validation

Release metadata is fixed at `0.1.0`; the package version, project version, and initial release tag must agree. Install with a fresh, non-editable install before validating the generated console command. The test suite checks that the command is installed under the active interpreter's `sysconfig` scripts directory.

The CI matrix checks Python 3.10 and 3.13 on Ubuntu and Windows. It installs pytest for development, installs this package non-editably, and runs the complete test suite with zero skips, including the installed console-command check. Tests use only synthetic values.

The source archive should contain every tracked project file and correspond exactly to the release tag and package metadata. An independent environment should install the published archive and run the adversarial suite before publication. These steps are release gates, not claims that a package has already been published.
