Configuration information for each experiment site

The `sensors` element controls which sensors classes are loaded when sensors.py is run 
  Configuration for each sensor type is shown below.
  
The `map` element is used to control the conversion between map coordinates and svg image coordinates

Example
=======================================================================================================
```yaml
UH Robot House:
  sensors:
  - type: ZigBee
    udp_listen_port: 5000
  - type: GEOSystem
    geo_server: geo-eee-pc
    geo_user: guest
    geo_password: password
    geo_db: livewiredb
    geo_query: CALL expPower
  - type: ZigBeeDirect
    usb_port: /dev/ttyUSB0
  - type: ZWaveVeraLite
    zwave_ip: 192.168.1.109
    zwave_port: 80
  - type: ZWaveHomeController
    zwave_ip: 192.168.1.109
  map:
    base: RobotHouseMap.svg
    svg_scale: 0.275
    svg_offset: 
      x: 81
      y: 245
    svg_rotation: -90
    # pgm_ should match values defined in map.yaml from ros_nav
    pgm_scale: 0.05
    pgm_offset:
      x: -8
      y: -19.2
```
