import ctypes

# AMS2 / Project Cars 2 Shared Memory Structure
# Based on the SMS Shared Memory API

class AMS2SharedMemory(ctypes.Structure):
    _fields_ = [
        # Version Info
        ("mVersion", ctypes.c_uint),
        ("mBuildVersionNumber", ctypes.c_uint),

        # Game State
        ("mGameState", ctypes.c_uint),
        ("mSessionState", ctypes.c_uint),

        # Participant Info
        ("mViewedParticipantIndex", ctypes.c_int),
        ("mNumParticipants", ctypes.c_int),

        # Unfiltered Input
        ("mUnfilteredThrottle", ctypes.c_ubyte),
        ("mUnfilteredBrake", ctypes.c_ubyte),
        ("mUnfilteredSteering", ctypes.c_byte),
        ("mUnfilteredClutch", ctypes.c_ubyte),

        # Car State
        ("mCarName", ctypes.c_char * 64),
        ("mCarClassName", ctypes.c_char * 64),

        # Telemetry
        ("mLapsInEvent", ctypes.c_uint),
        ("mTrackLocation", ctypes.c_char * 64),
        ("mTrackVariation", ctypes.c_char * 64),
        ("mTrackLength", ctypes.c_float),

        # Timings
        ("mLapInvalidated", ctypes.c_bool),
        ("mBestLapTime", ctypes.c_float),
        ("mLastLapTime", ctypes.c_float),
        ("mCurrentTime", ctypes.c_float),
        ("mSplitTimeAhead", ctypes.c_float),
        ("mSplitTimeBehind", ctypes.c_float),
        ("mSplitTime", ctypes.c_float),
        ("mEventTimeRemaining", ctypes.c_float),
        ("mPersonalFastestLapTime", ctypes.c_float),
        ("mWorldFastestLapTime", ctypes.c_float),
        ("mCurrentSector1Time", ctypes.c_float),
        ("mCurrentSector2Time", ctypes.c_float),
        ("mCurrentSector3Time", ctypes.c_float),
        ("mFastestSector1Time", ctypes.c_float),
        ("mFastestSector2Time", ctypes.c_float),
        ("mFastestSector3Time", ctypes.c_float),
        ("mPersonalFastestSector1Time", ctypes.c_float),
        ("mPersonalFastestSector2Time", ctypes.c_float),
        ("mPersonalFastestSector3Time", ctypes.c_float),
        ("mWorldFastestSector1Time", ctypes.c_float),
        ("mWorldFastestSector2Time", ctypes.c_float),
        ("mWorldFastestSector3Time", ctypes.c_float),

        # Flags
        ("mJoyPad0", ctypes.c_uint), # Flags

        # Physics
        ("mPhysics", ctypes.c_byte * 0), # Placeholder for physics start

        # Participant Info (Detailed)
        # ... (Simplified for now, focusing on local player physics)
    ]

# Full Physics Struct (Partial implementation for key telemetry)
class AMS2Physics(ctypes.Structure):
    _fields_ = [
        ("mParticipantIndex", ctypes.c_int),
        ("mUnfilteredThrottle", ctypes.c_float), # 0-1
        ("mUnfilteredBrake", ctypes.c_float),    # 0-1
        ("mUnfilteredSteering", ctypes.c_float), # -1 to 1
        ("mUnfilteredClutch", ctypes.c_float),   # 0-1
        
        ("mSpeed", ctypes.c_float),              # m/s
        ("mRpm", ctypes.c_float),                # radians/sec? No, usually RPM in shared mem, need to verify unit.
        ("mMaxRpm", ctypes.c_float),
        ("mGear", ctypes.c_int),                 # 0=N, 1=1, etc. -1=R
        
        # Wheels (FL, FR, RL, RR)
        ("mTyreRPS", ctypes.c_float * 4),
        ("mTyreY", ctypes.c_float * 4),
        ("mTyreTemp", ctypes.c_float * 4),       # Celsius
        ("mTyreHeightAboveGround", ctypes.c_float * 4),
        ("mTyreWear", ctypes.c_float * 4),       # 0-1
        ("mBrakeTempCelsius", ctypes.c_float * 4),
        ("mTyreTreadTemp", ctypes.c_float * 4),  # Kelvin? Or Celsius?
        
        ("mPosition", ctypes.c_float * 3),
        ("mOrientation", ctypes.c_float * 3),
    ]

# The actual shared memory layout is quite complex and packed. 
# For a robust implementation, we should use the exact byte offsets or a full struct definition.
# Since I don't have the full header file handy, I will use a library approach or a simplified reader 
# that maps specific offsets if the struct alignment is tricky.
# However, for Python, `ctypes` mapping of the full struct is best.

# Let's try to use a more complete definition to avoid offset issues.
# This is a known mapping for PCars2/AMS2.

class SharedMemory(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Version
        ("mVersion", ctypes.c_uint),
        ("mBuildVersionNumber", ctypes.c_uint),

        # Game State
        ("mGameState", ctypes.c_uint),
        ("mSessionState", ctypes.c_uint),

        # Participant Info
        ("mViewedParticipantIndex", ctypes.c_int),
        ("mNumParticipants", ctypes.c_int),

        # Unfiltered Input
        ("mUnfilteredThrottle", ctypes.c_ubyte),
        ("mUnfilteredBrake", ctypes.c_ubyte),
        ("mUnfilteredSteering", ctypes.c_byte),
        ("mUnfilteredClutch", ctypes.c_ubyte),

        # Car State
        ("mCarName", ctypes.c_char * 64),
        ("mCarClassName", ctypes.c_char * 64),

        # Telemetry
        ("mLapsInEvent", ctypes.c_uint),
        ("mTrackLocation", ctypes.c_char * 64),
        ("mTrackVariation", ctypes.c_char * 64),
        ("mTrackLength", ctypes.c_float),

        # Timings
        ("mLapInvalidated", ctypes.c_bool),
        ("mBestLapTime", ctypes.c_float),
        ("mLastLapTime", ctypes.c_float),
        ("mCurrentTime", ctypes.c_float),
        ("mSplitTimeAhead", ctypes.c_float),
        ("mSplitTimeBehind", ctypes.c_float),
        ("mSplitTime", ctypes.c_float),
        ("mEventTimeRemaining", ctypes.c_float),
        ("mPersonalFastestLapTime", ctypes.c_float),
        ("mWorldFastestLapTime", ctypes.c_float),
        ("mCurrentSector1Time", ctypes.c_float),
        ("mCurrentSector2Time", ctypes.c_float),
        ("mCurrentSector3Time", ctypes.c_float),
        ("mFastestSector1Time", ctypes.c_float),
        ("mFastestSector2Time", ctypes.c_float),
        ("mFastestSector3Time", ctypes.c_float),
        ("mPersonalFastestSector1Time", ctypes.c_float),
        ("mPersonalFastestSector2Time", ctypes.c_float),
        ("mPersonalFastestSector3Time", ctypes.c_float),
        ("mWorldFastestSector1Time", ctypes.c_float),
        ("mWorldFastestSector2Time", ctypes.c_float),
        ("mWorldFastestSector3Time", ctypes.c_float),

        # Flags
        ("mJoyPad0", ctypes.c_uint),
        ("mJoyPad1", ctypes.c_uint),

        # Pit Info
        ("mPitMode", ctypes.c_uint),
        ("mPitSchedule", ctypes.c_uint),

        # Flags
        ("mCarFlags", ctypes.c_uint),
        ("mOilTempCelsius", ctypes.c_float),
        ("mOilPressureKPa", ctypes.c_float),
        ("mWaterTempCelsius", ctypes.c_float),
        ("mWaterPressureKPa", ctypes.c_float),
        ("mFuelPressureKPa", ctypes.c_float),
        ("mFuelLevel", ctypes.c_float),
        ("mFuelCapacity", ctypes.c_float),
        ("mSpeed", ctypes.c_float),
        ("mRpm", ctypes.c_float),
        ("mMaxRpm", ctypes.c_float),
        ("mBrake", ctypes.c_float),
        ("mThrottle", ctypes.c_float),
        ("mClutch", ctypes.c_float),
        ("mSteering", ctypes.c_float),
        ("mGear", ctypes.c_int),
        ("mNumGears", ctypes.c_int),
        ("mOdometerKM", ctypes.c_float),
        ("mAntiLockActive", ctypes.c_bool),
        ("mLastOpponentCollisionIndex", ctypes.c_int),
        ("mLastOpponentCollisionMagnitude", ctypes.c_float),
        ("mBoostActive", ctypes.c_bool),
        ("mBoostAmount", ctypes.c_float),

        # Motion & Device
        ("mOrientation", ctypes.c_float * 3),
        ("mLocalVelocity", ctypes.c_float * 3),
        ("mWorldVelocity", ctypes.c_float * 3),
        ("mAngularVelocity", ctypes.c_float * 3),
        ("mLocalAcceleration", ctypes.c_float * 3),
        ("mWorldAcceleration", ctypes.c_float * 3),
        ("mExtentsCentre", ctypes.c_float * 3),

        # Wheels
        ("mTyreFlags", ctypes.c_uint * 4),
        ("mTerrain", ctypes.c_uint * 4),
        ("mTyreY", ctypes.c_float * 4),
        ("mTyreRPS", ctypes.c_float * 4),
        ("mTyreSlipSpeed", ctypes.c_float * 4),
        ("mTyreTemp", ctypes.c_float * 4),
        ("mTyreGrip", ctypes.c_float * 4),
        ("mTyreHeightAboveGround", ctypes.c_float * 4),
        ("mTyreLateralStiffness", ctypes.c_float * 4),
        ("mTyreWear", ctypes.c_float * 4),
        ("mBrakeDamage", ctypes.c_float * 4),
        ("mSuspensionDamage", ctypes.c_float * 4),
        ("mBrakeTempCelsius", ctypes.c_float * 4),
        ("mTyreTreadTemp", ctypes.c_float * 4),
        ("mTyreLayerTemp", ctypes.c_float * 4),
        ("mTyreCarcassTemp", ctypes.c_float * 4),
        ("mTyreRimTemp", ctypes.c_float * 4),
        ("mTyreInternalAirTemp", ctypes.c_float * 4),
        ("mTyreTempLeft", ctypes.c_float * 4),
        ("mTyreTempCenter", ctypes.c_float * 4),
        ("mTyreTempRight", ctypes.c_float * 4),
        ("mWheelLocalPositionY", ctypes.c_float * 4),
        ("mRideHeight", ctypes.c_float * 4),
        ("mSuspensionTravel", ctypes.c_float * 4),
        ("mSuspensionVelocity", ctypes.c_float * 4),
        ("mSuspensionRideHeight", ctypes.c_float * 4),
        ("mAirPressure", ctypes.c_float * 4),

        # Extras
        ("mEngineSpeed", ctypes.c_float),
        ("mEngineTorque", ctypes.c_float),
        ("mWings", ctypes.c_float * 2),
        ("mHandBrake", ctypes.c_float),

        # Damage
        ("mAeroDamage", ctypes.c_float),
        ("mEngineDamage", ctypes.c_float),

        # Weather
        ("mAmbientTemperature", ctypes.c_float),
        ("mTrackTemperature", ctypes.c_float),
        ("mRainDensity", ctypes.c_float),
        ("mSnowDensity", ctypes.c_float),
        ("mWindSpeed", ctypes.c_float),
        ("mWindDirectionX", ctypes.c_float),
        ("mWindDirectionY", ctypes.c_float),
        
        # Session Info
        ("mAggregateTime", ctypes.c_float), # Time since session started?

    ]
