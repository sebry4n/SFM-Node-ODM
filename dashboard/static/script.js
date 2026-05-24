document.addEventListener('DOMContentLoaded', () => {
    const btnCapture = document.getElementById('btn-capture');
    const btnProcess = document.getElementById('btn-process');
    const logOutput = document.getElementById('log-output');

    const eventSource = new EventSource('/api/logs');
    eventSource.onmessage = function(event) {
        const span = document.createElement('span');
        span.textContent = `> ${event.data}`;
        logOutput.appendChild(span);
        logOutput.scrollTop = logOutput.scrollHeight;
    };

    btnCapture.addEventListener('click', async () => {
        btnCapture.disabled = true;
        btnCapture.style.opacity = '0.5';
        try {
            await fetch('/api/capture', { method: 'POST' });
        } catch (e) {
            console.error(e);
        }
        setTimeout(() => {
            btnCapture.disabled = false;
            btnCapture.style.opacity = '1';
        }, 30000); 
    });

    btnProcess.addEventListener('click', async () => {
        btnProcess.disabled = true;
        btnProcess.style.opacity = '0.5';
        try {
            await fetch('/api/process', { method: 'POST' });
        } catch (e) {
            console.error(e);
        }
        setTimeout(() => {
            btnProcess.disabled = false;
            btnProcess.style.opacity = '1';
        }, 10000);
    });
});
