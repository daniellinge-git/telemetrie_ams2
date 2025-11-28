import ctypes

# Constants from SharedMemory.h
SHARED_MEMORY_VERSION = 14
STRING_LENGTH_MAX = 64
STORED_PARTICIPANTS_MAX = 64
TYRE_MAX = 4
VEC_MAX = 3

# Helper types
Vec3 = ctypes.c_float * VEC_MAX
TyreFloat = ctypes.c_float * TYRE_MAX
TyreUint = ctypes.c_uint * TYRE_MAX
TyreString = (ctypes.c_char * 40) * TYRE_MAX # TYRE_COMPOUND_NAME_LENGTH_MAX = 40

class ParticipantInfo(ctypes.Structure):
    _fields_ = [
        ("mIsActive", ctypes.c_bool),
        ("mName", ctypes.c_char * STRING_LENGTH_MAX),
        ("mWorldPosition", Vec3),
        ("mCurrentLapDistance", ctypes.c_float),
        ("mRacePosition", ctypes.c_uint),
        ("mLapsCompleted", ctypes.c_uint),
        ("mCurrentLap", ctypes.c_uint),
        ("mCurrentSector", ctypes.c_int),
    ]

class SharedMemory(ctypes.Structure):
    # Based on SharedMemory.h (Version 14)
    # Note: We assume standard alignment/packing unless specified otherwise. 
    # If issues persist, we might need _pack_ = 1, but usually ctypes handles standard C struct layout well.
    # However, for game shared memory, it's often packed. Let's try without explicit pack first, 
    # as the header didn't specify it, but if it fails, we add _pack_ = 1.
    # Actually, looking at the previous file, it had _pack_ = 1. 
    # SMS/AMS2 shared memory is known to be packed.
    # Let's use _pack_ = 1 to be safe, as it's the standard for this API.
    # Wait, if I use pack=1 and the C++ compiler used default (4 or 8), it will be wrong.
    # But usually these APIs are designed to be packed.
    # I will stick to the previous file's convention of _pack_ = 1.
    _pack_ = 1
    
    _fields_ = [
        # Version Number
        ("mVersion", ctypes.c_uint),
        ("mBuildVersionNumber", ctypes.c_uint),

        # Game States
        ("mGameState", ctypes.c_uint),
        ("mSessionState", ctypes.c_uint),
        ("mRaceState", ctypes.c_uint),

        # Participant Info
        ("mViewedParticipantIndex", ctypes.c_int),
        ("mNumParticipants", ctypes.c_int),
        ("mParticipantInfo", ParticipantInfo * STORED_PARTICIPANTS_MAX),

        # Unfiltered Input
        ("mUnfilteredThrottle", ctypes.c_float),
        ("mUnfilteredBrake", ctypes.c_float),
        ("mUnfilteredSteering", ctypes.c_float),
        ("mUnfilteredClutch", ctypes.c_float),

        # Vehicle information
        ("mCarName", ctypes.c_char * STRING_LENGTH_MAX),
        ("mCarClassName", ctypes.c_char * STRING_LENGTH_MAX),

        # Event information
        ("mLapsInEvent", ctypes.c_uint),
        ("mTrackLocation", ctypes.c_char * STRING_LENGTH_MAX),
        ("mTrackVariation", ctypes.c_char * STRING_LENGTH_MAX),
        ("mTrackLength", ctypes.c_float),

        # Timings
        ("mNumSectors", ctypes.c_int),
        ("mLapInvalidated", ctypes.c_bool),
        ("mPadding1", ctypes.c_byte * 3), # Padding to align mBestLapTime
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
        ("mHighestFlagColour", ctypes.c_uint),
        ("mHighestFlagReason", ctypes.c_uint),

        # Pit Info
        ("mPitMode", ctypes.c_uint),
        ("mPitSchedule", ctypes.c_uint),

        # Car State
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
        ("mMaxRPM", ctypes.c_float),
        ("mBrake", ctypes.c_float),
        ("mThrottle", ctypes.c_float),
        ("mClutch", ctypes.c_float),
        ("mSteering", ctypes.c_float),
        ("mGear", ctypes.c_int),
        ("mNumGears", ctypes.c_int),
        ("mOdometerKM", ctypes.c_float),
        ("mAntiLockActive", ctypes.c_bool),
        ("mPadding2", ctypes.c_byte * 3), # Padding
        ("mLastOpponentCollisionIndex", ctypes.c_int),
        ("mLastOpponentCollisionMagnitude", ctypes.c_float),
        ("mBoostActive", ctypes.c_bool),
        ("mPadding3", ctypes.c_byte * 3), # Padding
        ("mBoostAmount", ctypes.c_float),

        # Motion & Device Related
        ("mOrientation", Vec3),
        ("mLocalVelocity", Vec3),
        ("mWorldVelocity", Vec3),
        ("mAngularVelocity", Vec3),
        ("mLocalAcceleration", Vec3),
        ("mWorldAcceleration", Vec3),
        ("mExtentsCentre", Vec3),

        # Wheels / Tyres
        ("mTyreFlags", TyreUint),
        ("mTerrain", TyreUint),
        ("mTyreY", TyreFloat),
        ("mTyreRPS", TyreFloat),
        ("mTyreSlipSpeed", TyreFloat),
        ("mTyreTemp", TyreFloat),
        ("mTyreGrip", TyreFloat),
        ("mTyreHeightAboveGround", TyreFloat),
        ("mTyreLateralStiffness", TyreFloat),
        ("mTyreWear", TyreFloat),
        ("mBrakeDamage", TyreFloat),
        ("mSuspensionDamage", TyreFloat),
        ("mBrakeTempCelsius", TyreFloat),
        ("mTyreTreadTemp", TyreFloat),
        ("mTyreLayerTemp", TyreFloat),
        ("mTyreCarcassTemp", TyreFloat),
        ("mTyreRimTemp", TyreFloat),
        ("mTyreInternalAirTemp", TyreFloat),

        # Car Damage
        ("mCrashState", ctypes.c_uint),
        ("mAeroDamage", ctypes.c_float),
        ("mEngineDamage", ctypes.c_float),

        # Weather
        ("mAmbientTemperature", ctypes.c_float),
        ("mTrackTemperature", ctypes.c_float),
        ("mRainDensity", ctypes.c_float),
        ("mWindSpeed", ctypes.c_float),
        ("mWindDirectionX", ctypes.c_float),
        ("mWindDirectionY", ctypes.c_float),
        ("mCloudBrightness", ctypes.c_float),

        # PCars2 additions start, version 8
        ("mSequenceNumber", ctypes.c_uint),
        ("mWheelLocalPositionY", TyreFloat),
        ("mSuspensionTravel", TyreFloat),
        ("mSuspensionVelocity", TyreFloat),
        ("mAirPressure", TyreFloat),
        ("mEngineSpeed", ctypes.c_float),
        ("mEngineTorque", ctypes.c_float),
        ("mWings", ctypes.c_float * 2),
        ("mHandBrake", ctypes.c_float),

        # Additional race variables
        ("mCurrentSector1Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mCurrentSector2Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mCurrentSector3Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mFastestSector1Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mFastestSector2Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mFastestSector3Times", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mFastestLapTimes", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mLastLapTimes", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mLapsInvalidated", ctypes.c_bool * STORED_PARTICIPANTS_MAX),
        ("mRaceStates", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mPitModes", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mOrientations", Vec3 * STORED_PARTICIPANTS_MAX),
        ("mSpeeds", ctypes.c_float * STORED_PARTICIPANTS_MAX),
        ("mCarNames", (ctypes.c_char * STRING_LENGTH_MAX) * STORED_PARTICIPANTS_MAX),
        ("mCarClassNames", (ctypes.c_char * STRING_LENGTH_MAX) * STORED_PARTICIPANTS_MAX),

        # Additional race variables (continued)
        ("mEnforcedPitStopLap", ctypes.c_int),
        ("mTranslatedTrackLocation", ctypes.c_char * STRING_LENGTH_MAX),
        ("mTranslatedTrackVariation", ctypes.c_char * STRING_LENGTH_MAX),
        ("mBrakeBias", ctypes.c_float),
        ("mTurboBoostPressure", ctypes.c_float),
        ("mTyreCompound", TyreString),
        ("mPitSchedules", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mHighestFlagColours", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mHighestFlagReasons", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mNationalities", ctypes.c_uint * STORED_PARTICIPANTS_MAX),
        ("mSnowDensity", ctypes.c_float),

        # AMS2 Additions (v10...)
        ("mSessionDuration", ctypes.c_float),
        ("mSessionAdditionalLaps", ctypes.c_int),
        ("mTyreTempLeft", TyreFloat),
        ("mTyreTempCenter", TyreFloat),
        ("mTyreTempRight", TyreFloat),
        ("mDrsState", ctypes.c_uint),
        ("mRideHeight", TyreFloat),
        ("mJoyPad0", ctypes.c_uint),
        ("mDPad", ctypes.c_uint),
        ("mAntiLockSetting", ctypes.c_int),
        ("mTractionControlSetting", ctypes.c_int),
        ("mErsDeploymentMode", ctypes.c_int),
        ("mErsAutoModeEnabled", ctypes.c_bool),
        ("mClutchTemp", ctypes.c_float),
        ("mClutchWear", ctypes.c_float),
        ("mClutchOverheated", ctypes.c_bool),
        ("mClutchSlipping", ctypes.c_bool),
        ("mYellowFlagState", ctypes.c_int),
        ("mSessionIsPrivate", ctypes.c_bool),
        ("mLaunchStage", ctypes.c_int),
    ]
