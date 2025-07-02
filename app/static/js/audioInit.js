import AudioCapture from './audioCapture.js';
import audioPlayer from './audioPlayer.js';

document.addEventListener('DOMContentLoaded', async () => {
    const audioCapture = new AudioCapture();
    const hablarBtn = document.getElementById('hablar-btn');
    
    if (hablarBtn) {

        await audioCapture.initializeRecording();
        await audioPlayer.initialize();

        hablarBtn.addEventListener('touchstart', async (e) => {
            e.preventDefault();
            audioCapture.startRecording();
        });

        hablarBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            audioCapture.stopRecording();
        });

        hablarBtn.addEventListener('mousedown', async (e) => {
            e.preventDefault();
            audioCapture.startRecording();
        });

        hablarBtn.addEventListener('mouseup', (e) => {
            e.preventDefault();
            audioCapture.stopRecording();
        });
    }
});