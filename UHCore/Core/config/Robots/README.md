Controls various magic strings that are specific to individual robot models
Structure is as follows:

```yaml
Robot Name:
  componentName:
    positions:
      name: robot specific name or value
      # I.E. raised: deliverup OR raised: [[0.0, 1.57, 3.142]]
      # ...other component specific settings...
```


Some component settings are:
```yaml
    tray:
        size: Activation range for the phidget sensors, in cm (COB Only)
    head:
      camera:
        topic: ROS topic to get the image from
        rotate:
          angle: when to rotate the image, in degrees
          distance: tolerance (angle+-distance)
          amount: how much to rotate by (img.rotate(amount))
    hostname:
        override: ROS_MASTER_URI
                  # used in robotFactory() constructor
                  # I.E. COB3.2 default is built as cob3-2-pc1, if override is set to cob3_2_pc1
                  # cob3_2_pc1 will be used instead
```

Example
=======================================================================================================
```yaml
Care-O-Bot 3.2:
  phidgets:
    topics:
    - /range_0
    - /range_1
    - /range_2
    - /range_3
    windowSize: 5
  tray:
    positions:
      raised: up
      lowered: down
    size: 20
  head:
    positions:
      front: front
      back: back
    camera:
      topic: /stereo/right/image_color/compressed
      rotate:
        angle: 180
        distance: 90
        amount: 180
```
