<TODO>
dependencies:
pip3 install nicegui
pip3 install pyserial
pip3 install matplotlib
pip3 install numpy
pip3 install plotly

working with PLUTO
on MAC:

edit config.txt "usb_ethernet_mode = ncm"

download most recent libiio release from github:https://github.com/analogdevicesinc/libiio/releases
add iio_info to path:
    run:
        echo 'export PATH="/Library/Frameworks/iio.framework/Tools:$PATH"' >> ~/.zshrc
        source ~/.zshrc
    test:
        which iio_info
pip3 install pyadi-iio

