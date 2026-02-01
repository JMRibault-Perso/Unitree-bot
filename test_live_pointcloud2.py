#!/usr/bin/env python3
"""
Live test of PointCloud2 decoder with G1 SLAM
Waits for robot to come online, starts SLAM, and monitors point clouds
"""

import sys
import asyncio
import json
import logging
import time

sys.path.insert(0, '.')
from g1_app.patches import lidar_decoder_patch  # Apply patch
from g1_app.utils.arp_discovery import discover_robot_ip

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Stats tracking
pointcloud_count = 0
total_points = 0
last_update = time.time()

def on_pointcloud(data):
    """Callback for point cloud messages"""
    global pointcloud_count, total_points, last_update
    
    try:
        # Data should contain the decoded point cloud
        point_count = data.get('point_count', 0)
        
        pointcloud_count += 1
        total_points += point_count
        
        # Log every 10 point clouds
        if pointcloud_count % 10 == 0:
            avg_points = total_points / pointcloud_count if pointcloud_count > 0 else 0
            elapsed = time.time() - last_update
            fps = 10.0 / elapsed if elapsed > 0 else 0
            
            logger.info(f"📊 Point clouds received: {pointcloud_count}, "
                       f"Avg points/cloud: {avg_points:.0f}, "
                       f"Rate: {fps:.1f} Hz")
            
            if point_count > 0:
                points = data.get('points')
                if points is not None and len(points) > 0:
                    logger.info(f"   Latest cloud: {point_count} points, "
                               f"Format: {data.get('format', 'unknown')}")
                    logger.info(f"   Sample point: [{points[0,0]:.3f}, {points[0,1]:.3f}, {points[0,2]:.3f}]")
            
            last_update = time.time()
        
        # Log first point cloud immediately
        if pointcloud_count == 1:
            logger.info(f"🎯 FIRST POINT CLOUD! {point_count} points, format: {data.get('format', 'unknown')}")
            if point_count > 0 and 'points' in data:
                logger.info(f"   Sample: {data['points'][0]}")
    
    except Exception as e:
        logger.error(f"Error in point cloud callback: {e}", exc_info=True)


async def main():
    logger.info("=" * 70)
    logger.info("G1 SLAM PointCloud2 Live Test")
    logger.info("=" * 70)
    
    # Discover robot IP automatically via ARP
    try:
        robot_ip = discover_robot_ip()
        logger.info(f"✅ Robot found at {robot_ip}")
    except RuntimeError as e:
        logger.error(f"❌ Discovery failed: {e}")
        return
    
    logger.info("")
    
    # Try to connect (will wait for robot to come online)
    max_retries = 30
    for attempt in range(max_retries):
        try:
            conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.LocalSTA,
                ip=robot_ip
            )
            
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Connecting...")
            await conn.connect()
            logger.info("✅ Connected to robot!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection failed: {e}, retrying in 5s...")
                await asyncio.sleep(5)
            else:
                logger.error("Could not connect to robot")
                return
    
    # Subscribe to point cloud topic
    logger.info("📡 Subscribing to point cloud topic...")
    conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/points', on_pointcloud)
    
    # Start SLAM mapping
    logger.info("🗺️  Starting SLAM mapping...")
    result = await conn.datachannel.pub_sub.publish_request_new(
        'rt/api/slam_operate/request',
        {
            'api_id': 1801,
            'parameter': json.dumps({'data': {'slam_type': 'indoor'}})
        }
    )
    
    logger.info(f"SLAM start result: {result.get('data', {}).get('data', 'unknown')}")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("Monitoring point clouds... (Press Ctrl+C to stop)")
    logger.info("=" * 70)
    logger.info("")
    
    # Monitor for 60 seconds
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("\nStopping...")
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total point clouds: {pointcloud_count}")
    if pointcloud_count > 0:
        avg = total_points / pointcloud_count
        logger.info(f"Average points per cloud: {avg:.0f}")
        logger.info(f"Total points processed: {total_points}")
    logger.info("=" * 70)


if __name__ == '__main__':
    asyncio.run(main())
