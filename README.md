# aperi-mech_test

Regression tests for [aper-mech](https://github.com/aperijake/aperi-mech), an open-source platform for computational mechanics.

## Prerequisites

Some tests build meshes using `gmsh` and then convert them to `exodus` format using a combination of `meshio` and `exodus.py` from `seacas`. Running in parallel requires `mpi` and checking results differences requires `exodiff` from `seacas`. Some packages can all be installed using `spack` and others are better installed with `conda` or `pip`.

### Install Spack

Follow the instructions at [https://spack.readthedocs.io/en/latest/getting_started.html](https://spack.readthedocs.io/en/latest/getting_started.html). In short, install the `spack` prerequisites, clone `spack`, and source the script for shell support.

### Find System Tools

```bash
# Add system compilers. e.g. gcc
spack compiler find

# Use external tools. e.g. cmake
spack external find
```

### Create a Spack Environment

```bash
# Create and activate a spack environment for the project
spack env create aperi-mech_test
spacktivate aperi-mech_test
```

#### Add and Install Required Packages

```bash
# If needed, specify a specific compiler. For example, add `%gcc@10.5.0` at the end of the `spack add` commands
spack add seacas
spack add openmpi
spack add py-pip

# Install Packages
spack concretize -f
spack install
```

### Add system package prerequisites
```bash
# Needed by gmsh
sudo apt update
sudo apt install libglu1-mesa
sudo apt install xorg
```

### Install `gmesh` and `meshio`

```bash
# Be sure to match the pip version with the python version.
# E.g. run `python --version` and `pip --version` and check they match
pip install gmsh
pip install meshio
pip install netCDF4 # needed by meshio
```
