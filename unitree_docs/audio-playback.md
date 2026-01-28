# Audio Playback

**Source:** https://support.unitree.com/home/en/G1_developer/audio_playback  
**Scraped:** 10127.845638696

---

# G1 - Audio Playback Instructions

The G1 audio playback function supports audio from either `recording directly within the mobile app` or `importing external audio files`. This document primarily covers the usage method for `importing external audio`.

## Function Location

[Unitree Explore APP] → [go] → [More Functions] → [Player]

## Version Information

### APP Version

  * Android: V1.6.1 or above
  * IOS: V1.6.1 or above



### Firmware Version

Upgrade the following three components:

  * Vul Service: Version 2.0.4.4 or above
  * Webrtc Bridge: Version 1.0.7.5 or above
  * Audio Hub: Version 1.0.1.0 or above



* * *

## Speech Synthesis Configuration

### Recommended Platform

It is recommended to use Alibaba Cloud's speech synthesis service:  
🔗 [Alibaba Cloud Speech Synthesis Console](https://nls-portal.console.aiiyun.com/app/567093/%E8%BF%90%E6%8E%A7%E5%88%87%E6%8D%A2%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%907)

* * *

## Audio File Specifications

### Format Requirements

  * **Format** : WAV
  * **Sample Rate** : 16kHz
  * **Channels** : `Mono` (The device only supports mono audio; stereo may cause playback issues)
  * **Speaker** : Stanley (All device audio uniformly uses this speaker)



### Recommendations

  * When synthesizing audio, set the volume to 100% to ensure maximum playback volume.



### Constraints

  * Audio file size must not exceed 10MB
  * Recording duration must not exceed 3 minutes



* * *
