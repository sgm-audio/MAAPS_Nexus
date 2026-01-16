/*
 * MAAPS Nexus VST3 Plugin Header
 *
 * VST3 plugin wrapper that communicates with Python backend via shared memory
 * for ultra-low latency multi-agent audio processing.
 *
 * Build instructions:
 * - Requires VST3 SDK from Steinberg
 * - CMake build system
 * - C++17 or later
 */

#pragma once

#include "public.sdk/source/vst/vstaudioeffect.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include "pluginterfaces/base/ibstream.h"

#include <atomic>
#include <memory>
#include <string>
#include <cstring>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

namespace Steinberg {
namespace Vst {

//-----------------------------------------------------------------------------
// Shared Memory Header Structure (must match Python implementation)
//-----------------------------------------------------------------------------
struct SharedMemoryHeader {
    uint32_t magic;          // 0x4D415053 ('MAPS')
    uint32_t version;        // 1
    uint64_t write_offset;   // Offset for writing
    uint64_t read_offset;    // Offset for reading
    uint32_t block_size;     // Number of samples per block
    uint32_t sample_rate;    // Sample rate
    uint32_t num_channels;   // Number of channels
    uint64_t block_id;       // Current block ID
    uint64_t status;         // Status flags (0=no data, 1=data available)
};

//-----------------------------------------------------------------------------
// Shared Memory Audio Buffer Manager
//-----------------------------------------------------------------------------
class SharedMemoryAudioBuffer {
public:
    SharedMemoryAudioBuffer(const std::string& shm_name, size_t shm_size);
    ~SharedMemoryAudioBuffer();

    bool open();
    void close();

    bool writeAudio(const float** audio, int32 numChannels, int32 numSamples);
    bool readAudio(float** audio, int32 numChannels, int32 numSamples);

    bool isConnected() const { return m_connected; }

private:
    std::string m_shmName;
    size_t m_shmSize;
    int m_shmFd;
    void* m_shmPtr;
    bool m_connected;

    static constexpr size_t HEADER_SIZE = 64;
    static constexpr uint32_t MAGIC_NUMBER = 0x4D415053;
    static constexpr uint32_t VERSION = 1;

    SharedMemoryHeader* getHeader();
    void updateHeader(const SharedMemoryHeader& header);
};

//-----------------------------------------------------------------------------
// Parameter IDs
//-----------------------------------------------------------------------------
enum MAAPSParams : ParamID {
    kBypassParam = 0,
    kEQBand1Gain,
    kEQBand2Gain,
    kEQBand3Gain,
    kEQBand4Gain,
    kEQBand5Gain,
    kEQBand6Gain,
    kEQBand7Gain,
    kCompThreshold,
    kCompRatio,
    kCompAttack,
    kCompRelease,
    kCompMakeup,
    kAIMode,          // 0=off, 1=inference, 2=training
    kCooperationScore,  // Read-only
    kNumParams
};

//-----------------------------------------------------------------------------
// MAAPS Nexus Processor (Audio Processing)
//-----------------------------------------------------------------------------
class MAAPSNexusProcessor : public AudioEffect {
public:
    MAAPSNexusProcessor();
    ~MAAPSNexusProcessor() override;

    // AudioEffect overrides
    tresult PLUGIN_API initialize(FUnknown* context) override;
    tresult PLUGIN_API terminate() override;
    tresult PLUGIN_API setActive(TBool state) override;
    tresult PLUGIN_API process(ProcessData& data) override;
    tresult PLUGIN_API setState(IBStream* state) override;
    tresult PLUGIN_API getState(IBStream* state) override;
    tresult PLUGIN_API setupProcessing(ProcessSetup& newSetup) override;
    tresult PLUGIN_API canProcessSampleSize(int32 symbolicSampleSize) override;

    static FUnknown* createInstance(void*) { return (IAudioProcessor*)new MAAPSNexusProcessor; }

private:
    // Shared memory for Python backend communication
    std::unique_ptr<SharedMemoryAudioBuffer> m_shmBuffer;

    // Parameters
    float m_bypass;
    float m_eqGains[7];
    float m_compThreshold;
    float m_compRatio;
    float m_compAttack;
    float m_compRelease;
    float m_compMakeup;
    float m_aiMode;
    float m_cooperationScore;

    // Processing state
    bool m_backendConnected;
    std::atomic<uint64_t> m_processedBlocks;
    double m_sampleRate;

    // Latency tracking
    std::atomic<double> m_avgLatencyMs;
    std::atomic<double> m_maxLatencyMs;

    // Methods
    bool connectToBackend();
    void disconnectFromBackend();
    void updateParameters(IParameterChanges* paramChanges);
    bool processAudioWithBackend(ProcessData& data);
    void processBypass(ProcessData& data);
};

//-----------------------------------------------------------------------------
// MAAPS Nexus Controller (UI and Parameters)
//-----------------------------------------------------------------------------
class MAAPSNexusController : public EditController {
public:
    MAAPSNexusController();
    ~MAAPSNexusController() override;

    // EditController overrides
    tresult PLUGIN_API initialize(FUnknown* context) override;
    tresult PLUGIN_API terminate() override;
    tresult PLUGIN_API setComponentState(IBStream* state) override;

    static FUnknown* createInstance(void*) { return (IEditController*)new MAAPSNexusController; }

private:
    // Add parameters to the controller
    void addParameters();
};

//-----------------------------------------------------------------------------
// SharedMemoryAudioBuffer Implementation
//-----------------------------------------------------------------------------

inline SharedMemoryAudioBuffer::SharedMemoryAudioBuffer(const std::string& shm_name, size_t shm_size)
    : m_shmName(shm_name)
    , m_shmSize(shm_size)
    , m_shmFd(-1)
    , m_shmPtr(nullptr)
    , m_connected(false)
{
}

inline SharedMemoryAudioBuffer::~SharedMemoryAudioBuffer()
{
    close();
}

inline bool SharedMemoryAudioBuffer::open()
{
    // Open POSIX shared memory
    m_shmFd = shm_open(m_shmName.c_str(), O_RDWR, 0666);
    if (m_shmFd == -1) {
        return false;
    }

    // Map shared memory
    m_shmPtr = mmap(nullptr, m_shmSize, PROT_READ | PROT_WRITE, MAP_SHARED, m_shmFd, 0);
    if (m_shmPtr == MAP_FAILED) {
        ::close(m_shmFd);
        m_shmFd = -1;
        return false;
    }

    // Verify magic number
    SharedMemoryHeader* header = getHeader();
    if (header->magic != MAGIC_NUMBER) {
        close();
        return false;
    }

    m_connected = true;
    return true;
}

inline void SharedMemoryAudioBuffer::close()
{
    if (m_shmPtr && m_shmPtr != MAP_FAILED) {
        munmap(m_shmPtr, m_shmSize);
        m_shmPtr = nullptr;
    }

    if (m_shmFd != -1) {
        ::close(m_shmFd);
        m_shmFd = -1;
    }

    m_connected = false;
}

inline SharedMemoryHeader* SharedMemoryAudioBuffer::getHeader()
{
    return static_cast<SharedMemoryHeader*>(m_shmPtr);
}

inline void SharedMemoryAudioBuffer::updateHeader(const SharedMemoryHeader& header)
{
    std::memcpy(m_shmPtr, &header, sizeof(SharedMemoryHeader));
}

inline bool SharedMemoryAudioBuffer::writeAudio(const float** audio, int32 numChannels, int32 numSamples)
{
    if (!m_connected) return false;

    SharedMemoryHeader* header = getHeader();

    // Calculate size needed
    size_t audioSize = numChannels * numSamples * sizeof(float);

    // Check if there's space
    size_t availableSize = m_shmSize - HEADER_SIZE;
    if (audioSize > availableSize) {
        return false;
    }

    // Get write offset
    uint64_t writeOffset = header->write_offset;

    // Wrap around if necessary
    if (writeOffset + audioSize > m_shmSize) {
        writeOffset = HEADER_SIZE;
    }

    // Write audio data (interleaved)
    float* dest = reinterpret_cast<float*>(static_cast<char*>(m_shmPtr) + writeOffset);
    for (int32 sample = 0; sample < numSamples; ++sample) {
        for (int32 channel = 0; channel < numChannels; ++channel) {
            *dest++ = audio[channel][sample];
        }
    }

    // Update header
    header->write_offset = writeOffset + audioSize;
    header->block_size = numSamples;
    header->num_channels = numChannels;
    header->block_id++;
    header->status = 1; // Data available

    return true;
}

inline bool SharedMemoryAudioBuffer::readAudio(float** audio, int32 numChannels, int32 numSamples)
{
    if (!m_connected) return false;

    SharedMemoryHeader* header = getHeader();

    // Check if data is available
    if (header->status == 0) {
        return false;
    }

    // Get read offset
    uint64_t readOffset = header->read_offset;

    // Calculate size
    size_t audioSize = numChannels * numSamples * sizeof(float);

    // Read audio data (deinterleave)
    const float* src = reinterpret_cast<const float*>(static_cast<const char*>(m_shmPtr) + readOffset);
    for (int32 sample = 0; sample < numSamples; ++sample) {
        for (int32 channel = 0; channel < numChannels; ++channel) {
            audio[channel][sample] = *src++;
        }
    }

    // Update read offset
    uint64_t newReadOffset = readOffset + audioSize;
    if (newReadOffset >= m_shmSize) {
        newReadOffset = HEADER_SIZE;
    }

    header->read_offset = newReadOffset;
    header->status = 0; // Data consumed

    return true;
}

} // namespace Vst
} // namespace Steinberg
