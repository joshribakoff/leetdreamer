// Shared audio playback for all animation templates
let currentAudio = null;

function playStepAudio(stepIndex) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    const audio = new Audio(`step_${stepIndex}.wav`);
    audio.volume = 1.0;
    currentAudio = audio;
    audio.play().catch(e => {
        console.log('Audio playback:', e.message);
    });
}
