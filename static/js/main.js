// StegoShield Frontend Controller - Interactive UI & Capacity/Quality/Integrity/Steganalysis Handlers

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Password Toggle Visibility ---
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'bi bi-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'bi bi-eye';
            }
        });
    });

    // --- Helper: Setup Drag & Drop Zone ---
    function setupDropzone(dropzoneId, inputId, promptId, previewContainerId, previewImgId, nameId, dimsId, removeBtnId, onFileSelect) {
        const dropzone = document.getElementById(dropzoneId);
        const input = document.getElementById(inputId);
        const prompt = document.getElementById(promptId);
        const previewContainer = document.getElementById(previewContainerId);
        const previewImg = document.getElementById(previewImgId);
        const nameEl = document.getElementById(nameId);
        const dimsEl = dimsId ? document.getElementById(dimsId) : null;
        const removeBtn = removeBtnId ? document.getElementById(removeBtnId) : null;

        if (!dropzone || !input) return;

        dropzone.addEventListener('click', (e) => {
            if (e.target.closest('button') !== removeBtn) {
                input.click();
            }
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                handleFile(files[0]);
            }
        });

        input.addEventListener('change', () => {
            if (input.files.length > 0) {
                handleFile(input.files[0]);
            }
        });

        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                input.value = '';
                previewContainer.classList.add('d-none');
                prompt.classList.remove('d-none');
                if (onFileSelect) onFileSelect(null);
            });
        }

        function handleFile(file) {
            if (!file.type.startsWith('image/')) {
                alert('Please select a valid image file (PNG / BMP).');
                return;
            }
            nameEl.textContent = file.name;
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                prompt.classList.add('d-none');
                previewContainer.classList.remove('d-none');

                if (dimsEl) {
                    const tempImg = new Image();
                    tempImg.onload = () => {
                        dimsEl.textContent = `${tempImg.width} x ${tempImg.height} px`;
                        if (onFileSelect) onFileSelect(file, tempImg.width, tempImg.height);
                    };
                    tempImg.src = e.target.result;
                } else {
                    if (onFileSelect) onFileSelect(file);
                }
            };
            reader.readAsDataURL(file);
        }
    }

    // --- 2. Embed Tab Logic & Capacity Calculator ---
    let currentCoverWidth = 0;
    let currentCoverHeight = 0;

    setupDropzone(
        'embedDropzone', 'coverImageInput', 'embedDropzonePrompt',
        'embedPreviewContainer', 'coverPreviewImg', 'coverImageName',
        'coverImageDims', 'removeCoverBtn',
        (file, width, height) => {
            if (file && width && height) {
                currentCoverWidth = width;
                currentCoverHeight = height;
                updateCapacityMeter();
            } else {
                currentCoverWidth = 0;
                currentCoverHeight = 0;
                updateCapacityMeter();
            }
        }
    );

    const secretTextInput = document.getElementById('secretTextInput');
    const lsbSelect = document.getElementById('lsbSelect');
    const secretCharCount = document.getElementById('secretCharCount');

    if (secretTextInput) {
        secretTextInput.addEventListener('input', () => {
            const byteLen = new TextEncoder().encode(secretTextInput.value).length;
            secretCharCount.textContent = `${secretTextInput.value.length} characters (${byteLen} Bytes)`;
            updateCapacityMeter();
        });
    }

    if (lsbSelect) {
        lsbSelect.addEventListener('change', updateCapacityMeter);
    }

    function formatBytes(bytes) {
        if (bytes <= 0) return '0 Bytes';
        if (bytes < 1024) return `${bytes} Bytes`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    function updateCapacityMeter() {
        const capacityPctText = document.getElementById('capacityPctText');
        const capacityProgressBar = document.getElementById('capacityProgressBar');

        const lblTotalCap = document.getElementById('lblTotalCap');
        const lblUsedCap = document.getElementById('lblUsedCap');
        const lblRemCap = document.getElementById('lblRemCap');
        const lblMsgSize = document.getElementById('lblMsgSize');

        const capacityErrorBanner = document.getElementById('capacityErrorBanner');
        const capacityErrorText = document.getElementById('capacityErrorText');
        const embedSubmitBtn = document.getElementById('embedSubmitBtn');

        if (!currentCoverWidth || !currentCoverHeight) {
            if (capacityPctText) capacityPctText.textContent = '0% Used';
            if (capacityProgressBar) capacityProgressBar.style.width = '0%';
            if (lblTotalCap) lblTotalCap.textContent = '0 Bytes';
            if (lblUsedCap) lblUsedCap.textContent = '0 Bytes';
            if (lblRemCap) lblRemCap.textContent = '0 Bytes';
            if (lblMsgSize) lblMsgSize.textContent = '0 Bytes';
            if (capacityErrorBanner) capacityErrorBanner.classList.add('d-none');
            if (embedSubmitBtn) embedSubmitBtn.disabled = false;
            return;
        }

        const lsbCount = parseInt(lsbSelect ? lsbSelect.value : 1, 10) || 1;
        const totalPixels = currentCoverWidth * currentCoverHeight;
        const totalCapacityBytes = Math.floor((totalPixels * 3 * lsbCount) / 8);
        const headerOverhead = 52;

        const messageBytes = new TextEncoder().encode(secretTextInput ? secretTextInput.value || '' : '').length;
        const usedCapacityBytes = messageBytes > 0 ? (messageBytes + headerOverhead) : 0;
        const remainingCapacityBytes = Math.max(0, totalCapacityBytes - usedCapacityBytes);

        const percent = Math.min(100, Math.round((usedCapacityBytes / totalCapacityBytes) * 100) || 0);

        if (lblTotalCap) lblTotalCap.textContent = formatBytes(totalCapacityBytes);
        if (lblUsedCap) lblUsedCap.textContent = formatBytes(usedCapacityBytes);
        if (lblRemCap) lblRemCap.textContent = formatBytes(remainingCapacityBytes);
        if (lblMsgSize) lblMsgSize.textContent = formatBytes(messageBytes);
        if (capacityPctText) capacityPctText.textContent = `${percent}% Used`;

        if (capacityProgressBar) capacityProgressBar.style.width = `${percent}%`;

        if (usedCapacityBytes > totalCapacityBytes) {
            if (capacityProgressBar) capacityProgressBar.className = 'progress-bar bg-danger';
            if (capacityErrorText) capacityErrorText.textContent = `Payload Exceeded Capacity: Message (${formatBytes(usedCapacityBytes)}) exceeds cover capacity (${formatBytes(totalCapacityBytes)}). Please upload a larger image or shorten message.`;
            if (capacityErrorBanner) capacityErrorBanner.classList.remove('d-none');
            if (embedSubmitBtn) embedSubmitBtn.disabled = true;
        } else if (percent > 80) {
            if (capacityProgressBar) capacityProgressBar.className = 'progress-bar bg-warning';
            if (capacityErrorBanner) capacityErrorBanner.classList.add('d-none');
            if (embedSubmitBtn) embedSubmitBtn.disabled = false;
        } else {
            if (capacityProgressBar) capacityProgressBar.className = 'progress-bar bg-cyber-gradient';
            if (capacityErrorBanner) capacityErrorBanner.classList.add('d-none');
            if (embedSubmitBtn) embedSubmitBtn.disabled = false;
        }
    }

    // Embed Form Submit Handler
    const embedForm = document.getElementById('embedForm');
    if (embedForm) {
        embedForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(embedForm);

            const placeholder = document.getElementById('embedPlaceholder');
            const spinner = document.getElementById('embedSpinner');
            const resultContainer = document.getElementById('embedResult');
            const submitBtn = document.getElementById('embedSubmitBtn');

            if (placeholder) placeholder.classList.add('d-none');
            if (resultContainer) resultContainer.classList.add('d-none');
            if (spinner) spinner.classList.remove('d-none');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch('/api/embed', { method: 'POST', body: formData });
                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;

                if (data.success) {
                    const stegoImg = document.getElementById('stegoResultImg');
                    const downloadBtn = document.getElementById('downloadStegoBtn');
                    if (stegoImg) stegoImg.src = data.stego_image_b64;
                    if (downloadBtn) downloadBtn.href = data.stego_image_b64;

                    const resPSNR = document.getElementById('resPSNR');
                    const resSSIM = document.getElementById('resSSIM');
                    const resMSE = document.getElementById('resMSE');

                    if (resPSNR) resPSNR.textContent = data.metrics.psnr.toFixed(2);
                    if (resSSIM) resSSIM.textContent = data.metrics.ssim.toFixed(4);
                    if (resMSE) resMSE.textContent = data.metrics.mse.toFixed(4);

                    const resCap = document.getElementById('resCapacityUsed');
                    const resPay = document.getElementById('resPayloadBytes');
                    const resMod = document.getElementById('resModifiedPixels');
                    const resMax = document.getElementById('resMaxDiff');

                    if (resCap) resCap.textContent = `${data.stats.used_percentage}%`;
                    if (resPay) resPay.textContent = `${data.stats.encrypted_payload_size_bytes} Bytes`;
                    if (resMod) resMod.textContent = data.metrics.modified_pixels.toLocaleString();
                    if (resMax) resMax.textContent = `±${data.metrics.max_pixel_diff}`;

                    if (resultContainer) resultContainer.classList.remove('d-none');
                } else {
                    alert(`Embedding Error: ${data.error}`);
                    if (placeholder) placeholder.classList.remove('d-none');
                }
            } catch (err) {
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                alert(`Error: ${err.message}`);
                if (placeholder) placeholder.classList.remove('d-none');
            }
        });
    }

    // --- 3. Extract Tab Logic ---
    setupDropzone(
        'extractDropzone', 'stegoImageInput', 'extractDropzonePrompt',
        'extractPreviewContainer', 'stegoPreviewImg', 'stegoImageName',
        null, 'removeStegoBtn'
    );

    const extractForm = document.getElementById('extractForm');
    if (extractForm) {
        extractForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(extractForm);

            const spinner = document.getElementById('extractSpinner');
            const resultContainer = document.getElementById('extractResultContainer');
            const successCard = document.getElementById('extractSuccessCard');
            const errorCard = document.getElementById('extractErrorCard');
            const submitBtn = document.getElementById('extractSubmitBtn');

            if (resultContainer) resultContainer.classList.add('d-none');
            if (successCard) successCard.classList.add('d-none');
            if (errorCard) errorCard.classList.add('d-none');
            if (spinner) spinner.classList.remove('d-none');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch('/api/extract', { method: 'POST', body: formData });
                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                if (resultContainer) resultContainer.classList.remove('d-none');

                if (data.success) {
                    const outputTxt = document.getElementById('decryptedMessageOutput');
                    const statusLbl = document.getElementById('extractStatusSuccessLabel');
                    const badgeLsb = document.getElementById('extractLsbBadge');

                    if (outputTxt) outputTxt.value = data.secret_message;
                    if (statusLbl) statusLbl.textContent = data.status || "Likely Unmodified";
                    if (badgeLsb) badgeLsb.textContent = `${data.lsb_count} LSB Bit${data.lsb_count > 1 ? 's' : ''}`;
                    if (successCard) successCard.classList.remove('d-none');
                } else {
                    const errTitle = document.getElementById('extractErrorStatusTitle');
                    const errText = document.getElementById('extractErrorText');
                    if (errTitle) errTitle.textContent = `Status: ${data.status || "Possible Tampering"}`;
                    if (errText) errText.textContent = data.error;
                    if (errorCard) errorCard.classList.remove('d-none');
                }
            } catch (err) {
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                if (resultContainer) resultContainer.classList.remove('d-none');
                const errTitle = document.getElementById('extractErrorStatusTitle');
                const errText = document.getElementById('extractErrorText');
                if (errTitle) errTitle.textContent = "Status: Corrupted / Extraction Failed";
                if (errText) errText.textContent = `Request failed: ${err.message}`;
                if (errorCard) errorCard.classList.remove('d-none');
            }
        });
    }

    // Copy Decrypted Message Button
    const copyBtn = document.getElementById('copyMessageBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const textarea = document.getElementById('decryptedMessageOutput');
            if (!textarea) return;
            textarea.select();
            navigator.clipboard.writeText(textarea.value);
            copyBtn.innerHTML = '<i class="bi bi-check me-1"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy';
            }, 2000);
        });
    }

    // --- 4. Tamper Simulation Logic ---
    const tamperSimForm = document.getElementById('tamperSimForm');
    if (tamperSimForm) {
        tamperSimForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(tamperSimForm);
            const simResultContainer = document.getElementById('simResultContainer');
            const simResultImg = document.getElementById('simResultImg');
            const simDownloadBtn = document.getElementById('simDownloadBtn');
            const simBadgeAction = document.getElementById('simBadgeAction');
            const simSubmitBtn = document.getElementById('simSubmitBtn');

            if (simSubmitBtn) {
                simSubmitBtn.disabled = true;
                simSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Simulating...';
            }

            try {
                const response = await fetch('/api/tamper/simulate', { method: 'POST', body: formData });
                const data = await response.json();

                if (simSubmitBtn) {
                    simSubmitBtn.disabled = false;
                    simSubmitBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-2"></i>Simulate Image Manipulation';
                }

                if (data.success) {
                    if (simResultImg) simResultImg.src = data.manipulated_image_b64;
                    if (simDownloadBtn) simDownloadBtn.href = data.manipulated_image_b64;
                    if (simBadgeAction) simBadgeAction.textContent = `Action Simulated: ${data.action}`;
                    if (simResultContainer) simResultContainer.classList.remove('d-none');
                } else {
                    alert(`Simulation Error: ${data.error}`);
                }
            } catch (err) {
                if (simSubmitBtn) {
                    simSubmitBtn.disabled = false;
                    simSubmitBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-2"></i>Simulate Image Manipulation';
                }
                alert(`Error: ${err.message}`);
            }
        });
    }

    // --- 5. Steganalysis Tab Logic ---
    setupDropzone(
        'analyzeDropzone', 'suspectImageInput', 'analyzeDropzonePrompt',
        'analyzePreviewContainer', 'suspectPreviewImg', 'suspectImageName',
        null, 'removeSuspectBtn'
    );

    const analyzeForm = document.getElementById('analyzeForm');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(analyzeForm);

            const placeholder = document.getElementById('analyzePlaceholder');
            const spinner = document.getElementById('analyzeSpinner');
            const resultContainer = document.getElementById('analyzeResultContainer');
            const submitBtn = document.getElementById('analyzeSubmitBtn');

            if (placeholder) placeholder.classList.add('d-none');
            if (resultContainer) resultContainer.classList.add('d-none');
            if (spinner) spinner.classList.remove('d-none');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch('/api/analyze', { method: 'POST', body: formData });
                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;

                if (data.success) {
                    const report = data.report;
                    const scoreText = document.getElementById('suspicionScoreText');
                    const riskBadge = document.getElementById('riskLevelBadge');

                    if (scoreText) scoreText.textContent = `${report.suspicion_score} / 100`;
                    if (riskBadge) {
                        riskBadge.textContent = report.indication;
                        riskBadge.className = `badge px-3 py-2 fs-6 bg-${report.risk_class}`;
                    }

                    const f = report.feature_values;
                    const zeroOneRatio = document.getElementById('lblZeroOneRatio');
                    const entropyLbl = document.getElementById('lblEntropy');
                    const redStats = document.getElementById('lblRedStats');
                    const greenStats = document.getElementById('lblGreenStats');
                    const blueStats = document.getElementById('lblBlueStats');
                    const avgCorr = document.getElementById('lblAvgCorr');
                    const chiAnomaly = document.getElementById('lblChiAnomaly');
                    const bitCounts = document.getElementById('lblBitCounts');

                    if (zeroOneRatio) zeroOneRatio.textContent = f.lsb_distribution.zero_one_ratio.toFixed(4);
                    if (entropyLbl) entropyLbl.textContent = f.lsb_distribution.shannon_entropy.toFixed(4);
                    if (redStats) redStats.textContent = `${f.rgb_stats.red.mean} / ${f.rgb_stats.red.std}`;
                    if (greenStats) greenStats.textContent = `${f.rgb_stats.green.mean} / ${f.rgb_stats.green.std}`;
                    if (blueStats) blueStats.textContent = `${f.rgb_stats.blue.mean} / ${f.rgb_stats.blue.std}`;

                    if (avgCorr) avgCorr.textContent = f.neighbor_correlation.avg_neighbor_corr.toFixed(4);
                    if (chiAnomaly) chiAnomaly.textContent = `${f.chi_square_povs.avg_chi_anomaly}%`;
                    if (bitCounts) bitCounts.textContent = `${f.lsb_distribution.zeros_count.toLocaleString()} / ${f.lsb_distribution.ones_count.toLocaleString()}`;

                    if (report.viva_explanations) {
                        const expRatio = document.getElementById('expRatioViva');
                        const expChi = document.getElementById('expChiViva');
                        const expCorr = document.getElementById('expCorrViva');
                        if (expRatio) expRatio.textContent = report.viva_explanations.zero_one_ratio;
                        if (expChi) expChi.textContent = report.viva_explanations.chi_square_povs;
                        if (expCorr) expCorr.textContent = report.viva_explanations.neighbor_correlation;
                    }

                    if (report.disclaimer) {
                        const disclaimerEl = document.getElementById('steganalysisDisclaimer');
                        if (disclaimerEl) disclaimerEl.textContent = report.disclaimer;
                    }

                    if (resultContainer) resultContainer.classList.remove('d-none');
                } else {
                    alert(`Steganalysis Failed: ${data.error}`);
                    if (placeholder) placeholder.classList.remove('d-none');
                }
            } catch (err) {
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                alert(`Error: ${err.message}`);
                if (placeholder) placeholder.classList.remove('d-none');
            }
        });
    }

    // --- 6. Image Comparison Tab Logic ---
    setupDropzone('compareCoverDropzone', 'compareCoverInput', 'compareCoverPrompt', 'compareCoverPreview', 'compareCoverImg', 'compareCoverName', null, null);
    setupDropzone('compareStegoDropzone', 'compareStegoInput', 'compareStegoPrompt', 'compareStegoPreview', 'compareStegoImg', 'compareStegoName', null, null);

    const compareForm = document.getElementById('compareForm');
    if (compareForm) {
        compareForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(compareForm);

            const spinner = document.getElementById('compareSpinner');
            const resultContainer = document.getElementById('compareResultContainer');
            const submitBtn = document.getElementById('compareSubmitBtn');

            if (resultContainer) resultContainer.classList.add('d-none');
            if (spinner) spinner.classList.remove('d-none');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch('/api/compare', { method: 'POST', body: formData });
                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;

                if (data.success) {
                    const m = data.metrics;
                    const cmpPSNR = document.getElementById('cmpPSNR');
                    const cmpSSIM = document.getElementById('cmpSSIM');
                    const cmpMSE = document.getElementById('cmpMSE');

                    if (cmpPSNR) cmpPSNR.textContent = `${m.psnr.toFixed(2)} dB`;
                    if (cmpSSIM) cmpSSIM.textContent = m.ssim.toFixed(4);
                    if (cmpMSE) cmpMSE.textContent = m.mse.toFixed(4);

                    if (m.explanations) {
                        const expMse = document.getElementById('expMseText');
                        const expPsnr = document.getElementById('expPsnrText');
                        const expSsim = document.getElementById('expSsimText');
                        if (expMse) expMse.textContent = m.explanations.mse;
                        if (expPsnr) expPsnr.textContent = m.explanations.psnr;
                        if (expSsim) expSsim.textContent = m.explanations.ssim;
                    }

                    const cmpDims = document.getElementById('cmpDims');
                    const cmpTotal = document.getElementById('cmpTotalPx');
                    const cmpMod = document.getElementById('cmpModPx');
                    const cmpPct = document.getElementById('cmpModPct');

                    if (cmpDims) cmpDims.textContent = m.dimensions;
                    if (cmpTotal) cmpTotal.textContent = m.total_pixels.toLocaleString();
                    if (cmpMod) cmpMod.textContent = m.modified_pixels.toLocaleString();
                    if (cmpPct) cmpPct.textContent = `${m.percent_pixels_modified}%`;

                    if (resultContainer) resultContainer.classList.remove('d-none');
                } else {
                    alert(`Comparison Failed: ${data.error}`);
                }
            } catch (err) {
                if (spinner) spinner.classList.add('d-none');
                if (submitBtn) submitBtn.disabled = false;
                alert(`Error: ${err.message}`);
            }
        });
    }

});
