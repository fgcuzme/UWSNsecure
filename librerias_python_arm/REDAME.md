Files for cross-compilation on Ubuntu 24

Extracting Python ARM libraries from the Raspberry Pi to the VM

2.1 A .tar folder is created containing all the files necessary for compiling .py files, and this folder is transferred via SSH to the virtual machine.


1. Download the file `scp sysroot_arm64_pyconfig.tar.gz` to the directory `fgcuzme@192.168.75.174:~/sysroot_arm64_pyconfig.tar.gz`

2.2 Extract the file to the virtual machine in the directory you created earlier:

`tar -xvzf sysroot_arm64_pyconfig.tar.gz -C ~/arm64-sysroot`

3. Preparing the cross-compilation environment:

`export SYSROOT=~/arm64-sysroot`
`export C_INCLUDE_PATH=$SYSROOT/usr/include`
`export LIBRARY_PATH=$SYSROOT/usr/lib`
`export PATH=$PATH:$SYSROOT/usr/bin`

Note: Copy these lines one by one.
