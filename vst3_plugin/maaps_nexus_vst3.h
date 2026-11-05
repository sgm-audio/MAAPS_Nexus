/**
 * MAAPS Nexus VST3 Plugin
 *
 * VST3 plugin that communicates with Python multi-agent system via shared memory.
 * Designed for <10ms latency audio processing.
 *
 * Architecture:
 * - VST3 plugin receives audio from DAW
 * - Writes to shared memory ring buffer
 * - Python agents process audio
 * - Reads processed audio from shared memory
 * - Returns to DAW
 */

#pragma once

#include "public.sdk/source/vst/vstaudioeffect.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include "pluginterfaces/vst/ivstprocesscontext.h"

#include <atomic>
#include <memory>
#include <string>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#endif

namespace Steinberg {
namespace Vst {

//------------------------------------------------------------------------
// Shared Memory Ring Buffer
//------------------------------------------------------------------------
class SharedMemoryBuffer
{
public:
    SharedMemoryBuffer(const char* name, size_t bufferSize, int numChannels)
        : bufferName(name)
        , bufferSize(bufferSize)
        , numChannels(numChannels)
        , shm(nullptr)
        , shmHandle(nullptr)
    {
        headerSize = 20;  // read_pos(8) + write_pos(8) + processing_flag(4)
        audioDataSize = bufferSize * numChannels * sizeof(float);
        totalSize = headerSize + audioDataSize;

        initializeSharedMemory();
    }

    ~SharedMemoryBuffer()
    {
        cleanup();
    }

    bool isValid() const { return shm != nullptr; }

    // Read header
    void readHeader(uint64_t& readPos, uint64_t& writePos, uint32_t& flag)
    {
        if (!shm) return;

        memcpy(&readPos, shm, 8);
        memcpy(&writePos, (char*)shm + 8, 8);
        memcpy(&flag, (char*)shm + 16, 4);
    }

    // Write header
    void writeHeader(uint64_t readPos, uint64_t writePos, uint32_t flag)
    {
        if (!shm) return;

        memcpy(shm, &readPos, 8);
        memcpy((char*)shm + 8, &writePos, 8);
        memcpy((char*)shm + 16, &flag, 4);
    }

    // Write audio samples
    bool writeAudio(const float** audio, int numSamples)
    {
        if (!shm) return false;

        uint64_t readPos, writePos, tempFlag;
        readHeader(readPos, writePos, tempFlag);

        // Calculate available space
        uint64_t available;
        if (writePos >= readPos) {
            available = bufferSize - (writePos - readPos);
        } else {
            available = readPos - writePos;
        }

        if (available < (uint64_t)numSamples) {
            return false;  // Buffer full
        }

        // Write audio data
        for (int i = 0; i < numSamples; i++) {
            uint64_t pos = (writePos + i) % bufferSize;
            size_t offset = headerSize + pos * numChannels * sizeof(float);

            for (int ch = 0; ch < numChannels; ch++) {
                float sample = audio[ch][i];
                memcpy((char*)shm + offset + ch * sizeof(float), &sample, sizeof(float));
            }
        }

        // Update write position
        uint64_t newWritePos = (writePos + numSamples) % bufferSize;
        writeHeader(readPos, newWritePos, 0);

        return true;
    }

    // Read audio samples
    bool readAudio(float** audio, int numSamples)
    {
        if (!shm) return false;

        uint64_t readPos, writePos, tempFlag;
        readHeader(readPos, writePos, tempFlag);

        // Calculate available samples
        uint64_t available;
        if (writePos >= readPos) {
            available = writePos - readPos;
        } else {
            available = bufferSize - readPos + writePos;
        }

        if (available < (uint64_t)numSamples) {
            return false;  // Not enough data
        }

        // Read audio data
        for (int i = 0; i < numSamples; i++) {
            uint64_t pos = (readPos + i) % bufferSize;
            size_t offset = headerSize + pos * numChannels * sizeof(float);

            for (int ch = 0; ch < numChannels; ch++) {
                memcpy(&audio[ch][i], (char*)shm + offset + ch * sizeof(float), sizeof(float));
            }
        }

        // Update read position
        uint64_t newReadPos = (readPos + numSamples) % bufferSize;
        writeHeader(newReadPos, writePos, 0);

        return true;
    }

private:
    void initializeSharedMemory()
    {
#ifdef _WIN32
        // Windows implementation
        shmHandle = CreateFileMappingA(
            INVALID_HANDLE_VALUE,
            NULL,
            PAGE_READWRITE,
            0,
            (DWORD)totalSize,
            bufferName.c_str()
        );

        if (shmHandle == NULL) {
            return;
        }

        shm = MapViewOfFile(
            shmHandle,
            FILE_MAP_ALL_ACCESS,
            0,
            0,
            totalSize
        );

        if (shm) {
            // Initialize header to zeros if newly created
            uint64_t readPos = 0, writePos = 0;
            uint32_t flag = 0;
            writeHeader(readPos, writePos, flag);
        }
#else
        // POSIX implementation
        int fd = shm_open(bufferName.c_str(), O_CREAT | O_RDWR, 0666);
        if (fd == -1) {
            return;
        }

        ftruncate(fd, totalSize);

        shm = mmap(NULL, totalSize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);

        if (shm == MAP_FAILED) {
            shm = nullptr;
            return;
        }

        // Initialize header
        uint64_t readPos = 0, writePos = 0;
        uint32_t flag = 0;
        writeHeader(readPos, writePos, flag);
#endif
    }

    void cleanup()
    {
#ifdef _WIN32
        if (shm) {
            UnmapViewOfFile(shm);
            shm = nullptr;
        }
        if (shmHandle) {
            CloseHandle(shmHandle);
            shmHandle = nullptr;
        }
#else
        if (shm) {
            munmap(shm, totalSize);
            shm = nullptr;
        }
#endif
    }

    std::string bufferName;
    size_t bufferSize;
    int numChannels;
    size_t headerSize;
    size_t audioDataSize;
    size_t totalSize;

    void* shm;

#ifdef _WIN32
    HANDLE shmHandle;
#endif
};

//------------------------------------------------------------------------
// MAAPS Nexus VST3 Processor
//------------------------------------------------------------------------
class MAAPSNexusProcessor : public AudioEffect
{
public:
    MAAPSNexusProcessor()
        : inputBuffer(nullptr)
        , outputBuffer(nullptr)
        , bypass(false)
    {
    }

    ~MAAPSNexusProcessor()
    {
    }

    static FUnknown* createInstance(void* /*context*/)
    {
        return (IAudioProcessor*)new MAAPSNexusProcessor;
    }

    tresult PLUGIN_API initialize(FUnknown* context) SMTG_OVERRIDE
    {
        tresult result = AudioEffect::initialize(context);
        if (result != kResultOk) {
            return result;
        }

        // Add audio input/output
        addAudioInput(STR16("Stereo In"), SpeakerArr::kStereo);
        addAudioOutput(STR16("Stereo Out"), SpeakerArr::kStereo);

        // Initialize shared memory buffers
        inputBuffer = std::make_unique<SharedMemoryBuffer>(
            "maaps_nexus_buffer_input",
            8192,  // Buffer size
            2      // Stereo
        );

        outputBuffer = std::make_unique<SharedMemoryBuffer>(
            "maaps_nexus_buffer_output",
            8192,
            2
        );

        return kResultOk;
    }

    tresult PLUGIN_API terminate() SMTG_OVERRIDE
    {
        inputBuffer.reset();
        outputBuffer.reset();

        return AudioEffect::terminate();
    }

    tresult PLUGIN_API setActive(TBool state) SMTG_OVERRIDE
    {
        return AudioEffect::setActive(state);
    }

    tresult PLUGIN_API process(ProcessData& data) SMTG_OVERRIDE
    {
        // Check if bypass
        if (bypass || !inputBuffer || !outputBuffer) {
            // Bypass: copy input to output
            if (data.numInputs > 0 && data.numOutputs > 0) {
                int32 numChannels = data.inputs[0].numChannels;
                for (int32 ch = 0; ch < numChannels; ch++) {
                    if (data.inputs[0].channelBuffers32[ch] && data.outputs[0].channelBuffers32[ch]) {
                        memcpy(
                            data.outputs[0].channelBuffers32[ch],
                            data.inputs[0].channelBuffers32[ch],
                            data.numSamples * sizeof(float)
                        );
                    }
                }
            }
            return kResultOk;
        }

        // Process audio through shared memory
        int32 numSamples = data.numSamples;
        int32 numChannels = data.inputs[0].numChannels;

        // Write input to shared memory
        const float* inputChannels[2] = {
            data.inputs[0].channelBuffers32[0],
            numChannels > 1 ? data.inputs[0].channelBuffers32[1] : data.inputs[0].channelBuffers32[0]
        };

        bool writeSuccess = inputBuffer->writeAudio(inputChannels, numSamples);

        // Read processed audio from shared memory
        float* outputChannels[2] = {
            data.outputs[0].channelBuffers32[0],
            numChannels > 1 ? data.outputs[0].channelBuffers32[1] : data.outputs[0].channelBuffers32[0]
        };

        bool readSuccess = outputBuffer->readAudio(outputChannels, numSamples);

        // If read failed (no processed audio yet), use input as output
        if (!readSuccess || !writeSuccess) {
            for (int32 ch = 0; ch < numChannels; ch++) {
                memcpy(
                    data.outputs[0].channelBuffers32[ch],
                    data.inputs[0].channelBuffers32[ch],
                    numSamples * sizeof(float)
                );
            }
        }

        return kResultOk;
    }

    tresult PLUGIN_API setupProcessing(ProcessSetup& newSetup) SMTG_OVERRIDE
    {
        return AudioEffect::setupProcessing(newSetup);
    }

    tresult PLUGIN_API canProcessSampleSize(int32 symbolicSampleSize) SMTG_OVERRIDE
    {
        if (symbolicSampleSize == kSample32) {
            return kResultTrue;
        }
        return kResultFalse;
    }

protected:
    std::unique_ptr<SharedMemoryBuffer> inputBuffer;
    std::unique_ptr<SharedMemoryBuffer> outputBuffer;
    bool bypass;
};

//------------------------------------------------------------------------
} // namespace Vst
} // namespace Steinberg
