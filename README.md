# UWSNsecure
Test code for simulating the authentication process using a lightweight Tangle and data encryption with ASCON

Python version used:
3.11.5

Packages used:
Package      Version
------------ -------
ascon        0.0.9
cffi         1.17.1
cryptography 43.0.3
numpy        1.25.2
pip          24.3.1
pycparser    2.22
scipy        1.14.1
setuptools   65.5.0

*********************

Python to C conversion

Cross-compilation for ARM

1.- Creating the directory containing all ARM Python libraries

mkdir ~/arm64-sysroot

2.- Extracting ARM Python libraries from the Raspberry Pi to the VM

  2.1 Create a .tar archive that compresses all the files needed to compile .py files, and transfer it to the virtual machine via SSH:

  scp sysroot_arm64_pyconfig.tar.gz fgcuzme@192.168.75.174:~/sysroot_arm64_pyconfig.tar.gz

  Note: The file sysroot_arm64_pyconfig.tar.gz was created after multiple tests to gather all required dependencies. It will be available in the OneDrive repository for use.
  
  2.2 Extract the archive in the VM into the directory created earlier:
  
  tar -xvzf sysroot_arm64_pyconfig.tar.gz -C ~/arm64-sysroot
  
3.- Setting up the cross-compilation environment
  
  export SYSROOT=~/arm64-sysroot
  export C_INCLUDE_PATH=$SYSROOT/usr/include
  export LIBRARY_PATH=$SYSROOT/usr/lib
  export PATH=$PATH:$SYSROOT/usr/bin
    
  Note: These variables must be exported one by one.


RUNNING THE CODE ON THE RASPBERRY

1. Copy the entire folder from Ubuntu to the Raspberry Pi, except for the environment.

2. On the Raspberry Pi, create the environment and install the dependencies from the .txt file.

3. Convert the .so files to ARM so they can run on the Raspberry Pi. This step only needs to be repeated.

python setup.py build_ext --inplace

4. Force the execution of the folders

export PYTHONPATH=$(pwd)/venv_embed_rasp/lib/python3.11/site-packages:$PYTHONPATH
export LD_LIBRARY_PATH=$(pwd)/venv_embed_rasp/lib/python3.11/site-packages:$LD_LIBRARY_PATH

“venv2” should be replaced with the virtual environment you created.

5. Run main.
python3 a_run_many.py  -> this file call to simulation_test1_light_arm
