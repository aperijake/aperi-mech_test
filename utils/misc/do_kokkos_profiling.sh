#!/bin/bash

export KOKKOS_TOOLS_LIBS=/home/azureuser/projects/kokkos-tools_install/lib/libkp_kernel_timer.so;
/home/azureuser/projects/aperi-mech/build/RelWithDebInfo/aperi-mech input.yaml

# /home/azureuser/projects/kokkos-tools_install/bin/kp_reader AperiAzureGPU1-5393.dat > AperiAzureGPU1-5393.txt
