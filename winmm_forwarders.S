.text
.globl _proxy_CloseDriver
_proxy_CloseDriver:
  pushl $_proxy_name_CloseDriver
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DefDriverProc
_proxy_DefDriverProc:
  pushl $_proxy_name_DefDriverProc
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DriverCallback
_proxy_DriverCallback:
  pushl $_proxy_name_DriverCallback
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvClose
_proxy_DrvClose:
  pushl $_proxy_name_DrvClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvDefDriverProc
_proxy_DrvDefDriverProc:
  pushl $_proxy_name_DrvDefDriverProc
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvGetModuleHandle
_proxy_DrvGetModuleHandle:
  pushl $_proxy_name_DrvGetModuleHandle
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvOpen
_proxy_DrvOpen:
  pushl $_proxy_name_DrvOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvOpenA
_proxy_DrvOpenA:
  pushl $_proxy_name_DrvOpenA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_DrvSendMessage
_proxy_DrvSendMessage:
  pushl $_proxy_name_DrvSendMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_GetDriverFlags
_proxy_GetDriverFlags:
  pushl $_proxy_name_GetDriverFlags
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_GetDriverModuleHandle
_proxy_GetDriverModuleHandle:
  pushl $_proxy_name_GetDriverModuleHandle
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_OpenDriver
_proxy_OpenDriver:
  pushl $_proxy_name_OpenDriver
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_OpenDriverA
_proxy_OpenDriverA:
  pushl $_proxy_name_OpenDriverA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_PlaySound
_proxy_PlaySound:
  pushl $_proxy_name_PlaySound
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_PlaySoundA
_proxy_PlaySoundA:
  pushl $_proxy_name_PlaySoundA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_PlaySoundW
_proxy_PlaySoundW:
  pushl $_proxy_name_PlaySoundW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_SendDriverMessage
_proxy_SendDriverMessage:
  pushl $_proxy_name_SendDriverMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxGetDevCapsA
_proxy_auxGetDevCapsA:
  pushl $_proxy_name_auxGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxGetDevCapsW
_proxy_auxGetDevCapsW:
  pushl $_proxy_name_auxGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxGetNumDevs
_proxy_auxGetNumDevs:
  pushl $_proxy_name_auxGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxGetVolume
_proxy_auxGetVolume:
  pushl $_proxy_name_auxGetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxOutMessage
_proxy_auxOutMessage:
  pushl $_proxy_name_auxOutMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_auxSetVolume
_proxy_auxSetVolume:
  pushl $_proxy_name_auxSetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyConfigChanged
_proxy_joyConfigChanged:
  pushl $_proxy_name_joyConfigChanged
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetDevCapsA
_proxy_joyGetDevCapsA:
  pushl $_proxy_name_joyGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetDevCapsW
_proxy_joyGetDevCapsW:
  pushl $_proxy_name_joyGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetNumDevs
_proxy_joyGetNumDevs:
  pushl $_proxy_name_joyGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetPos
_proxy_joyGetPos:
  pushl $_proxy_name_joyGetPos
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetPosEx
_proxy_joyGetPosEx:
  pushl $_proxy_name_joyGetPosEx
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyGetThreshold
_proxy_joyGetThreshold:
  pushl $_proxy_name_joyGetThreshold
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joyReleaseCapture
_proxy_joyReleaseCapture:
  pushl $_proxy_name_joyReleaseCapture
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joySetCapture
_proxy_joySetCapture:
  pushl $_proxy_name_joySetCapture
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_joySetThreshold
_proxy_joySetThreshold:
  pushl $_proxy_name_joySetThreshold
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciDriverNotify
_proxy_mciDriverNotify:
  pushl $_proxy_name_mciDriverNotify
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciDriverYield
_proxy_mciDriverYield:
  pushl $_proxy_name_mciDriverYield
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciExecute
_proxy_mciExecute:
  pushl $_proxy_name_mciExecute
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciFreeCommandResource
_proxy_mciFreeCommandResource:
  pushl $_proxy_name_mciFreeCommandResource
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetCreatorTask
_proxy_mciGetCreatorTask:
  pushl $_proxy_name_mciGetCreatorTask
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetDeviceIDA
_proxy_mciGetDeviceIDA:
  pushl $_proxy_name_mciGetDeviceIDA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetDeviceIDFromElementIDA
_proxy_mciGetDeviceIDFromElementIDA:
  pushl $_proxy_name_mciGetDeviceIDFromElementIDA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetDeviceIDFromElementIDW
_proxy_mciGetDeviceIDFromElementIDW:
  pushl $_proxy_name_mciGetDeviceIDFromElementIDW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetDeviceIDW
_proxy_mciGetDeviceIDW:
  pushl $_proxy_name_mciGetDeviceIDW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetDriverData
_proxy_mciGetDriverData:
  pushl $_proxy_name_mciGetDriverData
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetErrorStringA
_proxy_mciGetErrorStringA:
  pushl $_proxy_name_mciGetErrorStringA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetErrorStringW
_proxy_mciGetErrorStringW:
  pushl $_proxy_name_mciGetErrorStringW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciGetYieldProc
_proxy_mciGetYieldProc:
  pushl $_proxy_name_mciGetYieldProc
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciLoadCommandResource
_proxy_mciLoadCommandResource:
  pushl $_proxy_name_mciLoadCommandResource
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSendCommandA
_proxy_mciSendCommandA:
  pushl $_proxy_name_mciSendCommandA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSendCommandW
_proxy_mciSendCommandW:
  pushl $_proxy_name_mciSendCommandW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSendStringA
_proxy_mciSendStringA:
  pushl $_proxy_name_mciSendStringA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSendStringW
_proxy_mciSendStringW:
  pushl $_proxy_name_mciSendStringW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSetDriverData
_proxy_mciSetDriverData:
  pushl $_proxy_name_mciSetDriverData
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mciSetYieldProc
_proxy_mciSetYieldProc:
  pushl $_proxy_name_mciSetYieldProc
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiConnect
_proxy_midiConnect:
  pushl $_proxy_name_midiConnect
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiDisconnect
_proxy_midiDisconnect:
  pushl $_proxy_name_midiDisconnect
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInAddBuffer
_proxy_midiInAddBuffer:
  pushl $_proxy_name_midiInAddBuffer
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInClose
_proxy_midiInClose:
  pushl $_proxy_name_midiInClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetDevCapsA
_proxy_midiInGetDevCapsA:
  pushl $_proxy_name_midiInGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetDevCapsW
_proxy_midiInGetDevCapsW:
  pushl $_proxy_name_midiInGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetErrorTextA
_proxy_midiInGetErrorTextA:
  pushl $_proxy_name_midiInGetErrorTextA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetErrorTextW
_proxy_midiInGetErrorTextW:
  pushl $_proxy_name_midiInGetErrorTextW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetID
_proxy_midiInGetID:
  pushl $_proxy_name_midiInGetID
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInGetNumDevs
_proxy_midiInGetNumDevs:
  pushl $_proxy_name_midiInGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInMessage
_proxy_midiInMessage:
  pushl $_proxy_name_midiInMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInOpen
_proxy_midiInOpen:
  pushl $_proxy_name_midiInOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInPrepareHeader
_proxy_midiInPrepareHeader:
  pushl $_proxy_name_midiInPrepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInReset
_proxy_midiInReset:
  pushl $_proxy_name_midiInReset
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInStart
_proxy_midiInStart:
  pushl $_proxy_name_midiInStart
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInStop
_proxy_midiInStop:
  pushl $_proxy_name_midiInStop
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiInUnprepareHeader
_proxy_midiInUnprepareHeader:
  pushl $_proxy_name_midiInUnprepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutCacheDrumPatches
_proxy_midiOutCacheDrumPatches:
  pushl $_proxy_name_midiOutCacheDrumPatches
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutCachePatches
_proxy_midiOutCachePatches:
  pushl $_proxy_name_midiOutCachePatches
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutClose
_proxy_midiOutClose:
  pushl $_proxy_name_midiOutClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetDevCapsA
_proxy_midiOutGetDevCapsA:
  pushl $_proxy_name_midiOutGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetDevCapsW
_proxy_midiOutGetDevCapsW:
  pushl $_proxy_name_midiOutGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetErrorTextA
_proxy_midiOutGetErrorTextA:
  pushl $_proxy_name_midiOutGetErrorTextA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetErrorTextW
_proxy_midiOutGetErrorTextW:
  pushl $_proxy_name_midiOutGetErrorTextW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetID
_proxy_midiOutGetID:
  pushl $_proxy_name_midiOutGetID
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetNumDevs
_proxy_midiOutGetNumDevs:
  pushl $_proxy_name_midiOutGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutGetVolume
_proxy_midiOutGetVolume:
  pushl $_proxy_name_midiOutGetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutLongMsg
_proxy_midiOutLongMsg:
  pushl $_proxy_name_midiOutLongMsg
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutMessage
_proxy_midiOutMessage:
  pushl $_proxy_name_midiOutMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutOpen
_proxy_midiOutOpen:
  pushl $_proxy_name_midiOutOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutPrepareHeader
_proxy_midiOutPrepareHeader:
  pushl $_proxy_name_midiOutPrepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutReset
_proxy_midiOutReset:
  pushl $_proxy_name_midiOutReset
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutSetVolume
_proxy_midiOutSetVolume:
  pushl $_proxy_name_midiOutSetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutShortMsg
_proxy_midiOutShortMsg:
  pushl $_proxy_name_midiOutShortMsg
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiOutUnprepareHeader
_proxy_midiOutUnprepareHeader:
  pushl $_proxy_name_midiOutUnprepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamClose
_proxy_midiStreamClose:
  pushl $_proxy_name_midiStreamClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamOpen
_proxy_midiStreamOpen:
  pushl $_proxy_name_midiStreamOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamOut
_proxy_midiStreamOut:
  pushl $_proxy_name_midiStreamOut
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamPause
_proxy_midiStreamPause:
  pushl $_proxy_name_midiStreamPause
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamPosition
_proxy_midiStreamPosition:
  pushl $_proxy_name_midiStreamPosition
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamProperty
_proxy_midiStreamProperty:
  pushl $_proxy_name_midiStreamProperty
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamRestart
_proxy_midiStreamRestart:
  pushl $_proxy_name_midiStreamRestart
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_midiStreamStop
_proxy_midiStreamStop:
  pushl $_proxy_name_midiStreamStop
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerClose
_proxy_mixerClose:
  pushl $_proxy_name_mixerClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetControlDetailsA
_proxy_mixerGetControlDetailsA:
  pushl $_proxy_name_mixerGetControlDetailsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetControlDetailsW
_proxy_mixerGetControlDetailsW:
  pushl $_proxy_name_mixerGetControlDetailsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetDevCapsA
_proxy_mixerGetDevCapsA:
  pushl $_proxy_name_mixerGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetDevCapsW
_proxy_mixerGetDevCapsW:
  pushl $_proxy_name_mixerGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetID
_proxy_mixerGetID:
  pushl $_proxy_name_mixerGetID
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetLineControlsA
_proxy_mixerGetLineControlsA:
  pushl $_proxy_name_mixerGetLineControlsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetLineControlsW
_proxy_mixerGetLineControlsW:
  pushl $_proxy_name_mixerGetLineControlsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetLineInfoA
_proxy_mixerGetLineInfoA:
  pushl $_proxy_name_mixerGetLineInfoA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetLineInfoW
_proxy_mixerGetLineInfoW:
  pushl $_proxy_name_mixerGetLineInfoW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerGetNumDevs
_proxy_mixerGetNumDevs:
  pushl $_proxy_name_mixerGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerMessage
_proxy_mixerMessage:
  pushl $_proxy_name_mixerMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerOpen
_proxy_mixerOpen:
  pushl $_proxy_name_mixerOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mixerSetControlDetails
_proxy_mixerSetControlDetails:
  pushl $_proxy_name_mixerSetControlDetails
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmGetCurrentTask
_proxy_mmGetCurrentTask:
  pushl $_proxy_name_mmGetCurrentTask
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmTaskBlock
_proxy_mmTaskBlock:
  pushl $_proxy_name_mmTaskBlock
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmTaskCreate
_proxy_mmTaskCreate:
  pushl $_proxy_name_mmTaskCreate
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmTaskSignal
_proxy_mmTaskSignal:
  pushl $_proxy_name_mmTaskSignal
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmTaskYield
_proxy_mmTaskYield:
  pushl $_proxy_name_mmTaskYield
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioAdvance
_proxy_mmioAdvance:
  pushl $_proxy_name_mmioAdvance
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioAscend
_proxy_mmioAscend:
  pushl $_proxy_name_mmioAscend
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioClose
_proxy_mmioClose:
  pushl $_proxy_name_mmioClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioCreateChunk
_proxy_mmioCreateChunk:
  pushl $_proxy_name_mmioCreateChunk
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioDescend
_proxy_mmioDescend:
  pushl $_proxy_name_mmioDescend
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioFlush
_proxy_mmioFlush:
  pushl $_proxy_name_mmioFlush
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioGetInfo
_proxy_mmioGetInfo:
  pushl $_proxy_name_mmioGetInfo
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioInstallIOProcA
_proxy_mmioInstallIOProcA:
  pushl $_proxy_name_mmioInstallIOProcA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioInstallIOProcW
_proxy_mmioInstallIOProcW:
  pushl $_proxy_name_mmioInstallIOProcW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioOpenA
_proxy_mmioOpenA:
  pushl $_proxy_name_mmioOpenA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioOpenW
_proxy_mmioOpenW:
  pushl $_proxy_name_mmioOpenW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioRead
_proxy_mmioRead:
  pushl $_proxy_name_mmioRead
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioRenameA
_proxy_mmioRenameA:
  pushl $_proxy_name_mmioRenameA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioRenameW
_proxy_mmioRenameW:
  pushl $_proxy_name_mmioRenameW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioSeek
_proxy_mmioSeek:
  pushl $_proxy_name_mmioSeek
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioSendMessage
_proxy_mmioSendMessage:
  pushl $_proxy_name_mmioSendMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioSetBuffer
_proxy_mmioSetBuffer:
  pushl $_proxy_name_mmioSetBuffer
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioSetInfo
_proxy_mmioSetInfo:
  pushl $_proxy_name_mmioSetInfo
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioStringToFOURCCA
_proxy_mmioStringToFOURCCA:
  pushl $_proxy_name_mmioStringToFOURCCA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioStringToFOURCCW
_proxy_mmioStringToFOURCCW:
  pushl $_proxy_name_mmioStringToFOURCCW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmioWrite
_proxy_mmioWrite:
  pushl $_proxy_name_mmioWrite
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_mmsystemGetVersion
_proxy_mmsystemGetVersion:
  pushl $_proxy_name_mmsystemGetVersion
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_sndPlaySoundA
_proxy_sndPlaySoundA:
  pushl $_proxy_name_sndPlaySoundA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_sndPlaySoundW
_proxy_sndPlaySoundW:
  pushl $_proxy_name_sndPlaySoundW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_timeGetSystemTime
_proxy_timeGetSystemTime:
  pushl $_proxy_name_timeGetSystemTime
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_timeKillEvent
_proxy_timeKillEvent:
  pushl $_proxy_name_timeKillEvent
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_timeSetEvent
_proxy_timeSetEvent:
  pushl $_proxy_name_timeSetEvent
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInAddBuffer
_proxy_waveInAddBuffer:
  pushl $_proxy_name_waveInAddBuffer
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInClose
_proxy_waveInClose:
  pushl $_proxy_name_waveInClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetDevCapsA
_proxy_waveInGetDevCapsA:
  pushl $_proxy_name_waveInGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetDevCapsW
_proxy_waveInGetDevCapsW:
  pushl $_proxy_name_waveInGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetErrorTextA
_proxy_waveInGetErrorTextA:
  pushl $_proxy_name_waveInGetErrorTextA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetErrorTextW
_proxy_waveInGetErrorTextW:
  pushl $_proxy_name_waveInGetErrorTextW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetID
_proxy_waveInGetID:
  pushl $_proxy_name_waveInGetID
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetNumDevs
_proxy_waveInGetNumDevs:
  pushl $_proxy_name_waveInGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInGetPosition
_proxy_waveInGetPosition:
  pushl $_proxy_name_waveInGetPosition
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInMessage
_proxy_waveInMessage:
  pushl $_proxy_name_waveInMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInOpen
_proxy_waveInOpen:
  pushl $_proxy_name_waveInOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInPrepareHeader
_proxy_waveInPrepareHeader:
  pushl $_proxy_name_waveInPrepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInReset
_proxy_waveInReset:
  pushl $_proxy_name_waveInReset
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInStart
_proxy_waveInStart:
  pushl $_proxy_name_waveInStart
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInStop
_proxy_waveInStop:
  pushl $_proxy_name_waveInStop
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveInUnprepareHeader
_proxy_waveInUnprepareHeader:
  pushl $_proxy_name_waveInUnprepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutBreakLoop
_proxy_waveOutBreakLoop:
  pushl $_proxy_name_waveOutBreakLoop
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutClose
_proxy_waveOutClose:
  pushl $_proxy_name_waveOutClose
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetDevCapsA
_proxy_waveOutGetDevCapsA:
  pushl $_proxy_name_waveOutGetDevCapsA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetDevCapsW
_proxy_waveOutGetDevCapsW:
  pushl $_proxy_name_waveOutGetDevCapsW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetErrorTextA
_proxy_waveOutGetErrorTextA:
  pushl $_proxy_name_waveOutGetErrorTextA
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetErrorTextW
_proxy_waveOutGetErrorTextW:
  pushl $_proxy_name_waveOutGetErrorTextW
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetID
_proxy_waveOutGetID:
  pushl $_proxy_name_waveOutGetID
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetNumDevs
_proxy_waveOutGetNumDevs:
  pushl $_proxy_name_waveOutGetNumDevs
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetPitch
_proxy_waveOutGetPitch:
  pushl $_proxy_name_waveOutGetPitch
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetPlaybackRate
_proxy_waveOutGetPlaybackRate:
  pushl $_proxy_name_waveOutGetPlaybackRate
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetPosition
_proxy_waveOutGetPosition:
  pushl $_proxy_name_waveOutGetPosition
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutGetVolume
_proxy_waveOutGetVolume:
  pushl $_proxy_name_waveOutGetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutMessage
_proxy_waveOutMessage:
  pushl $_proxy_name_waveOutMessage
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutOpen
_proxy_waveOutOpen:
  pushl $_proxy_name_waveOutOpen
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutPause
_proxy_waveOutPause:
  pushl $_proxy_name_waveOutPause
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutPrepareHeader
_proxy_waveOutPrepareHeader:
  pushl $_proxy_name_waveOutPrepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutReset
_proxy_waveOutReset:
  pushl $_proxy_name_waveOutReset
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutRestart
_proxy_waveOutRestart:
  pushl $_proxy_name_waveOutRestart
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutSetPitch
_proxy_waveOutSetPitch:
  pushl $_proxy_name_waveOutSetPitch
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutSetPlaybackRate
_proxy_waveOutSetPlaybackRate:
  pushl $_proxy_name_waveOutSetPlaybackRate
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutSetVolume
_proxy_waveOutSetVolume:
  pushl $_proxy_name_waveOutSetVolume
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutUnprepareHeader
_proxy_waveOutUnprepareHeader:
  pushl $_proxy_name_waveOutUnprepareHeader
  call _resolve_winmm_name@4
  jmp *%eax
.globl _proxy_waveOutWrite
_proxy_waveOutWrite:
  pushl $_proxy_name_waveOutWrite
  call _resolve_winmm_name@4
  jmp *%eax
.section .rdata,"dr"
_proxy_name_CloseDriver:
  .asciz "CloseDriver"
_proxy_name_DefDriverProc:
  .asciz "DefDriverProc"
_proxy_name_DriverCallback:
  .asciz "DriverCallback"
_proxy_name_DrvClose:
  .asciz "DrvClose"
_proxy_name_DrvDefDriverProc:
  .asciz "DrvDefDriverProc"
_proxy_name_DrvGetModuleHandle:
  .asciz "DrvGetModuleHandle"
_proxy_name_DrvOpen:
  .asciz "DrvOpen"
_proxy_name_DrvOpenA:
  .asciz "DrvOpenA"
_proxy_name_DrvSendMessage:
  .asciz "DrvSendMessage"
_proxy_name_GetDriverFlags:
  .asciz "GetDriverFlags"
_proxy_name_GetDriverModuleHandle:
  .asciz "GetDriverModuleHandle"
_proxy_name_OpenDriver:
  .asciz "OpenDriver"
_proxy_name_OpenDriverA:
  .asciz "OpenDriverA"
_proxy_name_PlaySound:
  .asciz "PlaySound"
_proxy_name_PlaySoundA:
  .asciz "PlaySoundA"
_proxy_name_PlaySoundW:
  .asciz "PlaySoundW"
_proxy_name_SendDriverMessage:
  .asciz "SendDriverMessage"
_proxy_name_auxGetDevCapsA:
  .asciz "auxGetDevCapsA"
_proxy_name_auxGetDevCapsW:
  .asciz "auxGetDevCapsW"
_proxy_name_auxGetNumDevs:
  .asciz "auxGetNumDevs"
_proxy_name_auxGetVolume:
  .asciz "auxGetVolume"
_proxy_name_auxOutMessage:
  .asciz "auxOutMessage"
_proxy_name_auxSetVolume:
  .asciz "auxSetVolume"
_proxy_name_joyConfigChanged:
  .asciz "joyConfigChanged"
_proxy_name_joyGetDevCapsA:
  .asciz "joyGetDevCapsA"
_proxy_name_joyGetDevCapsW:
  .asciz "joyGetDevCapsW"
_proxy_name_joyGetNumDevs:
  .asciz "joyGetNumDevs"
_proxy_name_joyGetPos:
  .asciz "joyGetPos"
_proxy_name_joyGetPosEx:
  .asciz "joyGetPosEx"
_proxy_name_joyGetThreshold:
  .asciz "joyGetThreshold"
_proxy_name_joyReleaseCapture:
  .asciz "joyReleaseCapture"
_proxy_name_joySetCapture:
  .asciz "joySetCapture"
_proxy_name_joySetThreshold:
  .asciz "joySetThreshold"
_proxy_name_mciDriverNotify:
  .asciz "mciDriverNotify"
_proxy_name_mciDriverYield:
  .asciz "mciDriverYield"
_proxy_name_mciExecute:
  .asciz "mciExecute"
_proxy_name_mciFreeCommandResource:
  .asciz "mciFreeCommandResource"
_proxy_name_mciGetCreatorTask:
  .asciz "mciGetCreatorTask"
_proxy_name_mciGetDeviceIDA:
  .asciz "mciGetDeviceIDA"
_proxy_name_mciGetDeviceIDFromElementIDA:
  .asciz "mciGetDeviceIDFromElementIDA"
_proxy_name_mciGetDeviceIDFromElementIDW:
  .asciz "mciGetDeviceIDFromElementIDW"
_proxy_name_mciGetDeviceIDW:
  .asciz "mciGetDeviceIDW"
_proxy_name_mciGetDriverData:
  .asciz "mciGetDriverData"
_proxy_name_mciGetErrorStringA:
  .asciz "mciGetErrorStringA"
_proxy_name_mciGetErrorStringW:
  .asciz "mciGetErrorStringW"
_proxy_name_mciGetYieldProc:
  .asciz "mciGetYieldProc"
_proxy_name_mciLoadCommandResource:
  .asciz "mciLoadCommandResource"
_proxy_name_mciSendCommandA:
  .asciz "mciSendCommandA"
_proxy_name_mciSendCommandW:
  .asciz "mciSendCommandW"
_proxy_name_mciSendStringA:
  .asciz "mciSendStringA"
_proxy_name_mciSendStringW:
  .asciz "mciSendStringW"
_proxy_name_mciSetDriverData:
  .asciz "mciSetDriverData"
_proxy_name_mciSetYieldProc:
  .asciz "mciSetYieldProc"
_proxy_name_midiConnect:
  .asciz "midiConnect"
_proxy_name_midiDisconnect:
  .asciz "midiDisconnect"
_proxy_name_midiInAddBuffer:
  .asciz "midiInAddBuffer"
_proxy_name_midiInClose:
  .asciz "midiInClose"
_proxy_name_midiInGetDevCapsA:
  .asciz "midiInGetDevCapsA"
_proxy_name_midiInGetDevCapsW:
  .asciz "midiInGetDevCapsW"
_proxy_name_midiInGetErrorTextA:
  .asciz "midiInGetErrorTextA"
_proxy_name_midiInGetErrorTextW:
  .asciz "midiInGetErrorTextW"
_proxy_name_midiInGetID:
  .asciz "midiInGetID"
_proxy_name_midiInGetNumDevs:
  .asciz "midiInGetNumDevs"
_proxy_name_midiInMessage:
  .asciz "midiInMessage"
_proxy_name_midiInOpen:
  .asciz "midiInOpen"
_proxy_name_midiInPrepareHeader:
  .asciz "midiInPrepareHeader"
_proxy_name_midiInReset:
  .asciz "midiInReset"
_proxy_name_midiInStart:
  .asciz "midiInStart"
_proxy_name_midiInStop:
  .asciz "midiInStop"
_proxy_name_midiInUnprepareHeader:
  .asciz "midiInUnprepareHeader"
_proxy_name_midiOutCacheDrumPatches:
  .asciz "midiOutCacheDrumPatches"
_proxy_name_midiOutCachePatches:
  .asciz "midiOutCachePatches"
_proxy_name_midiOutClose:
  .asciz "midiOutClose"
_proxy_name_midiOutGetDevCapsA:
  .asciz "midiOutGetDevCapsA"
_proxy_name_midiOutGetDevCapsW:
  .asciz "midiOutGetDevCapsW"
_proxy_name_midiOutGetErrorTextA:
  .asciz "midiOutGetErrorTextA"
_proxy_name_midiOutGetErrorTextW:
  .asciz "midiOutGetErrorTextW"
_proxy_name_midiOutGetID:
  .asciz "midiOutGetID"
_proxy_name_midiOutGetNumDevs:
  .asciz "midiOutGetNumDevs"
_proxy_name_midiOutGetVolume:
  .asciz "midiOutGetVolume"
_proxy_name_midiOutLongMsg:
  .asciz "midiOutLongMsg"
_proxy_name_midiOutMessage:
  .asciz "midiOutMessage"
_proxy_name_midiOutOpen:
  .asciz "midiOutOpen"
_proxy_name_midiOutPrepareHeader:
  .asciz "midiOutPrepareHeader"
_proxy_name_midiOutReset:
  .asciz "midiOutReset"
_proxy_name_midiOutSetVolume:
  .asciz "midiOutSetVolume"
_proxy_name_midiOutShortMsg:
  .asciz "midiOutShortMsg"
_proxy_name_midiOutUnprepareHeader:
  .asciz "midiOutUnprepareHeader"
_proxy_name_midiStreamClose:
  .asciz "midiStreamClose"
_proxy_name_midiStreamOpen:
  .asciz "midiStreamOpen"
_proxy_name_midiStreamOut:
  .asciz "midiStreamOut"
_proxy_name_midiStreamPause:
  .asciz "midiStreamPause"
_proxy_name_midiStreamPosition:
  .asciz "midiStreamPosition"
_proxy_name_midiStreamProperty:
  .asciz "midiStreamProperty"
_proxy_name_midiStreamRestart:
  .asciz "midiStreamRestart"
_proxy_name_midiStreamStop:
  .asciz "midiStreamStop"
_proxy_name_mixerClose:
  .asciz "mixerClose"
_proxy_name_mixerGetControlDetailsA:
  .asciz "mixerGetControlDetailsA"
_proxy_name_mixerGetControlDetailsW:
  .asciz "mixerGetControlDetailsW"
_proxy_name_mixerGetDevCapsA:
  .asciz "mixerGetDevCapsA"
_proxy_name_mixerGetDevCapsW:
  .asciz "mixerGetDevCapsW"
_proxy_name_mixerGetID:
  .asciz "mixerGetID"
_proxy_name_mixerGetLineControlsA:
  .asciz "mixerGetLineControlsA"
_proxy_name_mixerGetLineControlsW:
  .asciz "mixerGetLineControlsW"
_proxy_name_mixerGetLineInfoA:
  .asciz "mixerGetLineInfoA"
_proxy_name_mixerGetLineInfoW:
  .asciz "mixerGetLineInfoW"
_proxy_name_mixerGetNumDevs:
  .asciz "mixerGetNumDevs"
_proxy_name_mixerMessage:
  .asciz "mixerMessage"
_proxy_name_mixerOpen:
  .asciz "mixerOpen"
_proxy_name_mixerSetControlDetails:
  .asciz "mixerSetControlDetails"
_proxy_name_mmGetCurrentTask:
  .asciz "mmGetCurrentTask"
_proxy_name_mmTaskBlock:
  .asciz "mmTaskBlock"
_proxy_name_mmTaskCreate:
  .asciz "mmTaskCreate"
_proxy_name_mmTaskSignal:
  .asciz "mmTaskSignal"
_proxy_name_mmTaskYield:
  .asciz "mmTaskYield"
_proxy_name_mmioAdvance:
  .asciz "mmioAdvance"
_proxy_name_mmioAscend:
  .asciz "mmioAscend"
_proxy_name_mmioClose:
  .asciz "mmioClose"
_proxy_name_mmioCreateChunk:
  .asciz "mmioCreateChunk"
_proxy_name_mmioDescend:
  .asciz "mmioDescend"
_proxy_name_mmioFlush:
  .asciz "mmioFlush"
_proxy_name_mmioGetInfo:
  .asciz "mmioGetInfo"
_proxy_name_mmioInstallIOProcA:
  .asciz "mmioInstallIOProcA"
_proxy_name_mmioInstallIOProcW:
  .asciz "mmioInstallIOProcW"
_proxy_name_mmioOpenA:
  .asciz "mmioOpenA"
_proxy_name_mmioOpenW:
  .asciz "mmioOpenW"
_proxy_name_mmioRead:
  .asciz "mmioRead"
_proxy_name_mmioRenameA:
  .asciz "mmioRenameA"
_proxy_name_mmioRenameW:
  .asciz "mmioRenameW"
_proxy_name_mmioSeek:
  .asciz "mmioSeek"
_proxy_name_mmioSendMessage:
  .asciz "mmioSendMessage"
_proxy_name_mmioSetBuffer:
  .asciz "mmioSetBuffer"
_proxy_name_mmioSetInfo:
  .asciz "mmioSetInfo"
_proxy_name_mmioStringToFOURCCA:
  .asciz "mmioStringToFOURCCA"
_proxy_name_mmioStringToFOURCCW:
  .asciz "mmioStringToFOURCCW"
_proxy_name_mmioWrite:
  .asciz "mmioWrite"
_proxy_name_mmsystemGetVersion:
  .asciz "mmsystemGetVersion"
_proxy_name_sndPlaySoundA:
  .asciz "sndPlaySoundA"
_proxy_name_sndPlaySoundW:
  .asciz "sndPlaySoundW"
_proxy_name_timeGetSystemTime:
  .asciz "timeGetSystemTime"
_proxy_name_timeKillEvent:
  .asciz "timeKillEvent"
_proxy_name_timeSetEvent:
  .asciz "timeSetEvent"
_proxy_name_waveInAddBuffer:
  .asciz "waveInAddBuffer"
_proxy_name_waveInClose:
  .asciz "waveInClose"
_proxy_name_waveInGetDevCapsA:
  .asciz "waveInGetDevCapsA"
_proxy_name_waveInGetDevCapsW:
  .asciz "waveInGetDevCapsW"
_proxy_name_waveInGetErrorTextA:
  .asciz "waveInGetErrorTextA"
_proxy_name_waveInGetErrorTextW:
  .asciz "waveInGetErrorTextW"
_proxy_name_waveInGetID:
  .asciz "waveInGetID"
_proxy_name_waveInGetNumDevs:
  .asciz "waveInGetNumDevs"
_proxy_name_waveInGetPosition:
  .asciz "waveInGetPosition"
_proxy_name_waveInMessage:
  .asciz "waveInMessage"
_proxy_name_waveInOpen:
  .asciz "waveInOpen"
_proxy_name_waveInPrepareHeader:
  .asciz "waveInPrepareHeader"
_proxy_name_waveInReset:
  .asciz "waveInReset"
_proxy_name_waveInStart:
  .asciz "waveInStart"
_proxy_name_waveInStop:
  .asciz "waveInStop"
_proxy_name_waveInUnprepareHeader:
  .asciz "waveInUnprepareHeader"
_proxy_name_waveOutBreakLoop:
  .asciz "waveOutBreakLoop"
_proxy_name_waveOutClose:
  .asciz "waveOutClose"
_proxy_name_waveOutGetDevCapsA:
  .asciz "waveOutGetDevCapsA"
_proxy_name_waveOutGetDevCapsW:
  .asciz "waveOutGetDevCapsW"
_proxy_name_waveOutGetErrorTextA:
  .asciz "waveOutGetErrorTextA"
_proxy_name_waveOutGetErrorTextW:
  .asciz "waveOutGetErrorTextW"
_proxy_name_waveOutGetID:
  .asciz "waveOutGetID"
_proxy_name_waveOutGetNumDevs:
  .asciz "waveOutGetNumDevs"
_proxy_name_waveOutGetPitch:
  .asciz "waveOutGetPitch"
_proxy_name_waveOutGetPlaybackRate:
  .asciz "waveOutGetPlaybackRate"
_proxy_name_waveOutGetPosition:
  .asciz "waveOutGetPosition"
_proxy_name_waveOutGetVolume:
  .asciz "waveOutGetVolume"
_proxy_name_waveOutMessage:
  .asciz "waveOutMessage"
_proxy_name_waveOutOpen:
  .asciz "waveOutOpen"
_proxy_name_waveOutPause:
  .asciz "waveOutPause"
_proxy_name_waveOutPrepareHeader:
  .asciz "waveOutPrepareHeader"
_proxy_name_waveOutReset:
  .asciz "waveOutReset"
_proxy_name_waveOutRestart:
  .asciz "waveOutRestart"
_proxy_name_waveOutSetPitch:
  .asciz "waveOutSetPitch"
_proxy_name_waveOutSetPlaybackRate:
  .asciz "waveOutSetPlaybackRate"
_proxy_name_waveOutSetVolume:
  .asciz "waveOutSetVolume"
_proxy_name_waveOutUnprepareHeader:
  .asciz "waveOutUnprepareHeader"
_proxy_name_waveOutWrite:
  .asciz "waveOutWrite"
