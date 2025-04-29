## Install kernel
sudo apt install flex bison libssl-dev bc build-essential
libncurses5-dev libncursesw5-dev linux-headers-6.6.51+rpt-rpi-v6
git clone --depth=1 --branch rpi-6.6.y
https://github.com/raspberrypi/linux.git
## Make target directory
mkdir ~/tlv320aic3x_i2c_driver
cd ~/tlv320aic3x_i2c_driver
## Copy code
cp ~/linux/sound/soc/codecs/tlv320aic3x.c ~/tlv320aic3x_i2c_driver/
cp ~/linux/sound/soc/codecs/tlv320aic3x.h ~/tlv320aic3x_i2c_driver/
cp ~/linux/sound/soc/codecs/tlv320aic3x-i2c.c
~/tlv320aic3x_i2c_driver/
## Modify Makefile
nano Makefile
-------------------
obj-m += snd-soc-tlv320aic3x-i2c.o
snd-soc-tlv320aic3x-i2c-objs := tlv320aic3x.o tlv320aic3x-i2c.o
KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)
all:
$(MAKE) -C $(KDIR) M=$(PWD) modules
clean:
$(MAKE) -C $(KDIR) M=$(PWD) clean
install:
sudo cp snd-soc-tlv320aic3x-i2c.ko /lib/modules/$(shell
uname -r)/kernel/sound/soc/codecs/
sudo depmod -a
-------------------
## Compile the driver
make
sudo make install
https://wiki.seeedstudio.com/respeaker_2_mics_pi_hat_raspberry_v2/
3/124/29/25, 10:38 AM
Getting Started with Raspberry Pi | Seeed Studio Wiki
sudo modprobe snd-soc-tlv320aic3x-i2c
## Check logs
lsmod | grep tlv320
dmesg | grep tlv320
