import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { MTLLoader } from 'three/addons/loaders/MTLLoader.js';

document.addEventListener('DOMContentLoaded', () => {
    const btnCapture = document.getElementById('btn-capture');
    const btnProcess = document.getElementById('btn-process');
    const logOutput = document.getElementById('log-output');
    const cameraSelect = document.getElementById('camera-select');
    const datasetGallery = document.getElementById('dataset-gallery');
    const resultsUl = document.getElementById('results-ul');
    const viewerStatus = document.getElementById('viewer-status');

    // Logs SSE
    const eventSource = new EventSource('/api/logs');
    eventSource.onmessage = function(event) {
        const span = document.createElement('span');
        span.textContent = `> ${event.data}`;
        logOutput.appendChild(span);
        logOutput.scrollTop = logOutput.scrollHeight;
        if(event.data.includes("Capture selesai!")) refreshDataset();
        if(event.data.includes("Proses 3D Selesai!")) refreshResults();
    };

    // Actions
    btnCapture.addEventListener('click', async () => {
        btnCapture.disabled = true;
        btnCapture.style.opacity = '0.5';
        try { await fetch('/api/capture', { method: 'POST' }); } catch (e) { console.error(e); }
        setTimeout(() => { btnCapture.disabled = false; btnCapture.style.opacity = '1'; }, 30000); 
    });

    btnProcess.addEventListener('click', async () => {
        btnProcess.disabled = true;
        btnProcess.style.opacity = '0.5';
        try { await fetch('/api/process', { method: 'POST' }); } catch (e) { console.error(e); }
        setTimeout(() => { btnProcess.disabled = false; btnProcess.style.opacity = '1'; }, 10000);
    });

    // Camera Switch & Realtime Detection
    let knownCameras = "";

    async function fetchCameras() {
        try {
            const res = await fetch('/api/cameras');
            const data = await res.json();
            
            // Cek apakah ada perubahan daftar kamera atau kamera aktif
            const stateStr = JSON.stringify({cams: data.cameras, curr: data.current});
            if (stateStr !== knownCameras) {
                knownCameras = stateStr;
                cameraSelect.innerHTML = '';
                
                if(data.cameras.length === 0) {
                    cameraSelect.innerHTML = '<option value="0">Tidak Ada Kamera Terdeteksi</option>';
                } else {
                    data.cameras.forEach(cam => {
                        const opt = document.createElement('option');
                        opt.value = cam.index;
                        opt.textContent = cam.name;
                        if(cam.index === data.current) opt.selected = true;
                        cameraSelect.appendChild(opt);
                    });
                }
            }
        } catch(e) {
            console.error("Gagal mendeteksi kamera", e);
        }
    }

    // Panggil saat awal & poll tiap 3 detik
    fetchCameras();
    setInterval(fetchCameras, 3000);

    cameraSelect.addEventListener('change', async (e) => {
        await fetch('/api/camera/switch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index: e.target.value})
        });
    });

    // Dataset
    async function refreshDataset() {
        const res = await fetch('/api/dataset');
        const data = await res.json();
        datasetGallery.innerHTML = '';
        data.files.forEach(file => {
            const img = document.createElement('img');
            img.src = `/dataset/${file}?t=${new Date().getTime()}`;
            datasetGallery.appendChild(img);
        });
    }
    document.getElementById('btn-refresh-dataset').addEventListener('click', refreshDataset);
    refreshDataset();

    // Results & 3D Viewer
    async function refreshResults() {
        const res = await fetch('/api/results');
        const data = await res.json();
        resultsUl.innerHTML = '';
        let foundObj = null;
        let foundMtl = null;

        data.files.forEach(file => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `/assets/${file}`;
            a.target = "_blank";
            a.textContent = file;
            li.appendChild(a);
            resultsUl.appendChild(li);

            if(file.endsWith('.obj')) foundObj = file;
            if(file.endsWith('.mtl')) foundMtl = file;
        });

        if(foundObj) {
            viewerStatus.textContent = "Memuat 3D Model...";
            viewerStatus.style.display = 'block';
            load3DModel(foundObj, foundMtl);
        }
    }
    document.getElementById('btn-refresh-results').addEventListener('click', refreshResults);
    refreshResults();

    // Three.js Setup
    const container = document.getElementById('three-container');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 50;
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    let currentModel = null;

    function load3DModel(objPath, mtlPath) {
        if(currentModel) scene.remove(currentModel);
        
        const loadObj = (materials) => {
            const objLoader = new OBJLoader();
            if(materials) {
                materials.preload();
                objLoader.setMaterials(materials);
            }
            objLoader.load(`/assets/${objPath}`, (object) => {
                viewerStatus.style.display = 'none';
                currentModel = object;
                
                // Center model
                const box = new THREE.Box3().setFromObject(object);
                const center = box.getCenter(new THREE.Vector3());
                object.position.x += (object.position.x - center.x);
                object.position.y += (object.position.y - center.y);
                object.position.z += (object.position.z - center.z);
                
                // Scale model to fit within FOV
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const scale = 20 / maxDim;
                object.scale.set(scale, scale, scale);
                
                scene.add(object);
            }, undefined, (error) => {
                viewerStatus.textContent = "Gagal memuat OBJ";
                console.error(error);
            });
        };

        if(mtlPath) {
            const mtlLoader = new MTLLoader();
            const mtlDir = mtlPath.substring(0, mtlPath.lastIndexOf('/') + 1);
            mtlLoader.setResourcePath(`/assets/${mtlDir}`);
            mtlLoader.load(`/assets/${mtlPath}`, loadObj, undefined, (e) => loadObj(null));
        } else {
            loadObj(null);
        }
    }

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
});
