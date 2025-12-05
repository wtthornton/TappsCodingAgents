# Home Automation Protocols

## Protocol Selection Guide

### Zigbee
- **Best for**: Battery-powered devices, mesh networks, large device counts
- **Range**: 10-100m per device (mesh extends range)
- **Power**: Low (excellent for battery devices)
- **Use cases**: Sensors, switches, bulbs, door locks

### Z-Wave
- **Best for**: Reliable communication, security-focused applications
- **Range**: 30-100m per device (mesh extends range)
- **Power**: Low to medium
- **Use cases**: Security systems, door locks, garage door openers

### Matter (Thread/WiFi)
- **Best for**: Interoperability across ecosystems, modern devices
- **Range**: WiFi range (Thread mesh for low-power devices)
- **Power**: Variable (WiFi higher, Thread lower)
- **Use cases**: New devices, cross-platform compatibility

### WiFi
- **Best for**: High-bandwidth devices, direct cloud connectivity
- **Range**: Router-dependent (typically 30-50m)
- **Power**: Higher (requires constant power)
- **Use cases**: Cameras, smart displays, voice assistants

## Protocol Selection Decision Tree

1. **Battery-powered device?**
   - Yes → Zigbee or Z-Wave
   - No → Continue to #2

2. **Needs high bandwidth (video/audio)?**
   - Yes → WiFi
   - No → Continue to #3

3. **Needs cross-platform compatibility?**
   - Yes → Matter
   - No → Continue to #4

4. **Security critical?**
   - Yes → Z-Wave or Matter
   - No → Zigbee or WiFi

## Best Practices

- **Mesh Networks**: Zigbee and Z-Wave benefit from having multiple powered devices (routers) in the mesh
- **Hub Placement**: Place hubs centrally for best coverage
- **Device Density**: Limit to 30-50 Zigbee/Z-Wave devices per hub for optimal performance
- **Interference**: Keep 2.4GHz WiFi and Zigbee separated (use different channels)

