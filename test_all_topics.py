#!/usr/bin/env python3
"""
Test subscribing to ALL possible LiDAR/point cloud topic variations
to find which one actually publishes data
"""

import sys
import asyncio
import logging

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# All possible topic names for point cloud data
POSSIBLE_TOPICS = [
    # Standard LiDAR topics
    "rt/utlidar/cloud_livox_mid360",
    "rt/lidar/cloud",
    "rt/pointcloud",
    "rt/cloud",
    
    # SLAM-related topics
    "rt/slam/pointcloud",
    "rt/slam/cloud",
    "rt/slam_pointcloud",
    "rt/slam_cloud",
    
    # Alternative naming
    "rt/utlidar/pointcloud",
    "rt/utlidar/cloud",
    "rt/sensor/lidar",
    "rt/sensor/cloud",
    
    # Lower-level topics
    "rt/lf/lidar",
    "rt/lf/pointcloud",
    "rt/hf/lidar",
    "rt/hf/pointcloud",
]

received_topics = set()

async def main():
    global received_topics
    
    robot_ip = "192.168.86.18"
    robot_sn = "E21D1000PAHBMB06"
    
    logger.info(f"Connecting to robot {robot_sn} at {robot_ip}...")
    
    conn = UnitreeWebRTCConnection(
        peer_ip=robot_ip,
        peer_sn=robot_sn,
        connection_type=WebRTCConnectionMethod.LocalSTA
    )
    
    await conn.connect()
    logger.info("✓ Connected via WebRTC")
    
    # Create callback for each topic
    def make_callback(topic_name):
        def callback(data):
            if topic_name not in received_topics:
                logger.warning(f"🎯 DATA RECEIVED ON: {topic_name}")
                logger.warning(f"   Type: {type(data)}")
                if isinstance(data, dict):
                    logger.warning(f"   Keys: {list(data.keys())[:10]}")
                received_topics.add(topic_name)
        return callback
    
    # Subscribe to all possible topics
    logger.info(f"\n📡 Subscribing to {len(POSSIBLE_TOPICS)} possible topics...")
    for topic in POSSIBLE_TOPICS:
        try:
            conn.datachannel.pub_sub.subscribe(topic, make_callback(topic))
            logger.info(f"   ✓ Subscribed to: {topic}")
        except Exception as e:
            logger.warning(f"   ✗ Failed to subscribe to {topic}: {e}")
    
    # Wait for data
    logger.info("\n⏳ Waiting 60 seconds for data...")
    logger.info("   (SLAM mapping should be started for LiDAR to publish)")
    
    for i in range(60):
        await asyncio.sleep(1)
        if i % 10 == 0:
            logger.info(f"   {60-i} seconds remaining... (topics received: {len(received_topics)})")
    
    logger.info(f"\n📊 Results:")
    if received_topics:
        logger.info(f"   Topics that published data: {sorted(received_topics)}")
    else:
        logger.warning(f"   NO DATA RECEIVED on any topic!")
        logger.warning(f"   This means:")
        logger.warning(f"   1. Point cloud might not be published as DDS topic")
        logger.warning(f"   2. Might need special API call to enable streaming")
        logger.warning(f"   3. Data might come through different channel (video/file)")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
