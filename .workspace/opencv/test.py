import numpy as np
import argparse
import pyrealsense2 as rs



def main():
    p = argparse.ArgumentParser(
        description="RealSense Color Camera Example"
    )
    p.add_argument(
        '--serial',
        help='Serial number of the RealSense camera'
    )
    args = p.parse_args()

    devices = list(rs.context().query_devices())

    if not devices:
        print("No RealSense devices found")
        return

    # Print connected RealSense devices
    for d in devices:
        for key in (
            rs.camera_info.name,
            rs.camera_info.serial_number,
            rs.camera_info.usb_type_descriptor
        ):
            if d.supports(key):
                print(f"{key}: {d.get_info(key)}")

    # Require serial if multiple cameras are connected
    if len(devices) > 1 and not args.serial:
        raise SystemExit(
            "Multiple devices found. "
            "Please specify the serial number of the device to use."
        )

    config = rs.config()

    if args.serial:
        config.enable_device(args.serial)

    # Enable RGB/color stream
    config.enable_stream(
        rs.stream.color,
        640,
        480,
        rs.format.bgr8,
        30
    )

    pipeline = rs.pipeline()
    started = False

    try:
        pipeline.start(config)
        started = True

        frames = pipeline.wait_for_frames()
        color = frames.get_color_frame()

        if not color:
            raise RuntimeError("Could not acquire color frame")

        array = np.asanyarray(color.get_data())

        print("Color frame shape:", array.shape)

    except Exception as e:
        print("Error:", e)

    finally:
        if started:
            pipeline.stop()



if __name__ == "__main__":
    main()