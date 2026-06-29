# UWSNsecure
Test code for simulating the authentication process using a lightweight Tangle and data encryption with ASCON

Python version used (Ubuntu and Raspberry):
3.11.5

Packages used:
Package      Version
------------ -------
ascon           0.0.9
cffi            1.17.1
contourpy       1.3.3
cryptography    43.0.3
cycler          0.12.1
Cython          3.1.5
fonttools       4.60.1
kiwisolver      1.4.9
matplotlib      3.10.7
msgpack         1.1.2
numpy           1.25.2
packaging       25.0
pandas          2.3.3
pillow          12.0.0
pip             23.0.1
pycparser       2.22
pyparsing       3.2.5
python-dateutil 2.9.0.post0
pytz            2025.2
scipy           1.14.1
setuptools      66.1.1
six             1.17.0
tzdata          2025.2

*********************

#########################################
Python to C conversion (Ubuntu)

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

4. To verify the compilation, we will run the .main file, which in this case is “pyhon3.11 a_run_many.py”.

5. Run the setup as follows: python3.11 setup.py
This file contains the .py modules to be compiled with Cython.

7. If necessary, install Cython in the virtual environment using the pip command.

Once the files are converted, we will use Cython to transform our calling file into a .c file with the following command:

cython --embed -o simulation_test1_light.c simulation_test1_light.py --directive language_level=3

Replace “simulation_test1_light.c simulation_test1_light.py” with the files you want to convert. In this case, the main file.

7. Additionally, you need to import the library locations.

export PYTHONPATH=/home/fcuzme/arm64-sysroot/compilables_embed/embed_python/lib/python3.11/site-packages:$(pwd)

“/arm64-sysroot/compilables_embed/embed_python”, replace with your configured path.

8. Finally, we transform the .c file into an executable with the same name.

gcc -o simulation_test1_light simulation_test1_light.c -I/usr/include/python3.11 -L/usr/lib/x86_64-linux-gnu -lpython3.11 -lpthread -lm -lutil -ldl


###################################################

ARMx64 transformation (ubuntu)

We transform the .c file into ARM

aarch64-linux-gnu-gcc --sysroot=$SYSROOT -o simulation_test1_light_arm simulation_test1_light.c -I$SYSROOT/usr/include/aarch64-linux-gnu/python3.11 -L$SYSROOT/usr/lib/aarch64-linux-gnu -lpython3.11 -lpthread -lm -lutil -ldl

###################################################

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
