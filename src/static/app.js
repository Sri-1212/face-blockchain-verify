/**
 * HH Goa 2026 Task 3: Face Identification & Blockchain Verification
 * Frontend Orchestrator (Vanilla JS)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Restore the user's theme choice for this browser.
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('faceVerifyTheme');

  function applyTheme(theme) {
    const isLight = theme === 'light';
    document.documentElement.dataset.theme = isLight ? 'light' : 'dark';
    themeToggle.setAttribute('aria-pressed', String(isLight));
    themeToggle.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
    themeToggle.setAttribute('title', isLight ? 'Switch to dark theme' : 'Switch to light theme');
    themeToggle.querySelector('.theme-toggle-label').textContent = isLight ? 'Dark mode' : 'Light mode';
  }

  applyTheme(savedTheme === 'light' ? 'light' : 'dark');
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('faceVerifyTheme', nextTheme);
    applyTheme(nextTheme);
  });

  // DOM Elements
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const dropPrompt = document.getElementById('dropPrompt');
  const previewContainer = document.getElementById('previewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const previewFilename = document.getElementById('previewFilename');
  const previewFilesize = document.getElementById('previewFilesize');
  const btnReplace = document.getElementById('btnReplace');
  const btnVerify = document.getElementById('btnVerify');
  const verifyForm = document.getElementById('verifyForm');

  // Sample quick buttons
  const btnSampleSuccess = document.getElementById('btnSampleSuccess');
  const btnSampleFail = document.getElementById('btnSampleFail');

  // Progress Pipeline Elements
  const pipelineProgressCard = document.getElementById('pipelineProgressCard');
  const liveStatusText = document.getElementById('liveStatusText');
  const pipeStep1 = document.getElementById('pipeStep1');
  const pipeStep2 = document.getElementById('pipeStep2');
  const pipeStep3 = document.getElementById('pipeStep3');
  const pipeStep1Tag = document.getElementById('pipeStep1Tag');
  const pipeStep2Tag = document.getElementById('pipeStep2Tag');
  const pipeStep3Tag = document.getElementById('pipeStep3Tag');
  const pipeConn1 = document.getElementById('pipeConn1');
  const pipeConn2 = document.getElementById('pipeConn2');

  // Results Dashboard Elements
  const resultsDashboard = document.getElementById('resultsDashboard');
  const resFaceDim = document.getElementById('resFaceDim');
  const resTotalMatches = document.getElementById('resTotalMatches');
  const resSocialMatches = document.getElementById('resSocialMatches');
  const resPlatformBadge = document.getElementById('resPlatformBadge');
  const resMatchTitle = document.getElementById('resMatchTitle');
  const resMatchSource = document.getElementById('resMatchSource');
  const resMatchRank = document.getElementById('resMatchRank');
  const resMatchLink = document.getElementById('resMatchLink');
  const resRecordHashShort = document.getElementById('resRecordHashShort');
  const resBlockIndex = document.getElementById('resBlockIndex');
  const resBlockHash = document.getElementById('resBlockHash');
  const resChainLength = document.getElementById('resChainLength');
  const btnCopyHash = document.getElementById('btnCopyHash');
  const copyBtnText = document.getElementById('copyBtnText');
  const btnResetDashboard = document.getElementById('btnResetDashboard');

  // Error Card Elements
  const errorCard = document.getElementById('errorCard');
  const errorStageBadge = document.getElementById('errorStageBadge');
  const errorHeading = document.getElementById('errorHeading');
  const errorMessage = document.getElementById('errorMessage');
  const btnTryAnother = document.getElementById('btnTryAnother');
  const toast = document.getElementById('toast');

  // Application State
  let currentSelectedFile = null;
  let currentFullHash = '';
  let statusInterval = null;
  let progressStepTimer = null;

  // ---------------------------------------------------------------------------
  // Utility Functions
  // ---------------------------------------------------------------------------
  function formatBytes(bytes, decimals = 1) {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => {
      toast.classList.add('hidden');
    }, 2500);
  }

  function shortenHash(hash, lead = 14, tail = 8) {
    if (!hash || hash.length <= lead + tail) return hash;
    return `${hash.slice(0, lead)}...${hash.slice(-tail)}`;
  }

  function getPlatformClass(platform) {
    if (!platform) return 'other';
    const clean = platform.toLowerCase();
    if (clean.includes('instagram')) return 'instagram';
    if (clean.includes('linkedin')) return 'linkedin';
    if (clean.includes('twitter') || clean.includes('x')) return 'x-twitter';
    if (clean.includes('facebook')) return 'facebook';
    if (clean.includes('youtube')) return 'youtube';
    if (clean.includes('tiktok')) return 'tiktok';
    if (clean.includes('github')) return 'github';
    return 'other';
  }

  // ---------------------------------------------------------------------------
  // File Selection & Drag-and-Drop Handlers
  // ---------------------------------------------------------------------------
  function handleFileSelection(file) {
    if (!file) return;

    // Validate type
    const validExtensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValid && !file.type.startsWith('image/')) {
      alert('Please select a supported image file (JPG, PNG, WEBP).');
      return;
    }

    currentSelectedFile = file;

    // Read and preview
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      previewFilename.textContent = file.name;
      previewFilesize.textContent = formatBytes(file.size);

      dropPrompt.classList.add('hidden');
      previewContainer.classList.remove('hidden');
      btnVerify.removeAttribute('disabled');

      // Clear any prior results/errors
      resultsDashboard.classList.add('hidden');
      errorCard.classList.add('hidden');
    };
    reader.readAsDataURL(file);
  }

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  });

  // Drag and Drop Events
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelection(e.dataTransfer.files[0]);
    }
  });

  btnReplace.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  // ---------------------------------------------------------------------------
  // Quick Sample Photo Loaders
  // ---------------------------------------------------------------------------
  async function loadSampleImage(filename) {
    try {
      const response = await fetch(`/api/sample-images/${filename}`);
      if (!response.ok) {
        throw new Error('Could not fetch sample image from server.');
      }
      const blob = await response.blob();
      const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });

      // Create DataTransfer to update input
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;

      handleFileSelection(file);
    } catch (err) {
      console.error('Failed to load sample image:', err);
      alert(`Could not load sample image: ${filename}`);
    }
  }

  if (btnSampleSuccess) {
    btnSampleSuccess.addEventListener('click', () => {
      loadSampleImage('my_public_photo.jpg');
    });
  }

  if (btnSampleFail) {
    btnSampleFail.addEventListener('click', () => {
      loadSampleImage('no_face.jpg');
    });
  }

  // ---------------------------------------------------------------------------
  // Progress Pipeline Simulation & Updating
  // ---------------------------------------------------------------------------
  function resetPipelineSteps() {
    [pipeStep1, pipeStep2, pipeStep3].forEach(step => {
      step.className = 'pipeline-step waiting';
    });
    [pipeConn1, pipeConn2].forEach(conn => {
      conn.className = 'step-connector';
    });
    pipeStep1Tag.textContent = 'WAITING';
    pipeStep2Tag.textContent = 'WAITING';
    pipeStep3Tag.textContent = 'WAITING';
    if (statusInterval) clearInterval(statusInterval);
    if (progressStepTimer) clearTimeout(progressStepTimer);
  }

  function setStepState(stepElement, tagElement, state) {
    stepElement.className = `pipeline-step ${state}`;
    tagElement.textContent = state.toUpperCase();
  }

  function startPipelineAnimation() {
    resetPipelineSteps();
    pipelineProgressCard.classList.remove('hidden');

    const statusMessages = [
      "Detecting facial landmarks with DeepFace...",
      "Extracting 128-dimensional FaceNet embeddings...",
      "Uploading image temporarily to ImgBB...",
      "Querying SerpApi Google Lens for visual matches...",
      "Extracting publicly indexed social media matches...",
      "Computing canonical SHA-256 fingerprint...",
      "Committing record to immutable blockchain...",
      "Validating blockchain ledger integrity..."
    ];

    let msgIdx = 0;
    liveStatusText.textContent = statusMessages[0];
    statusInterval = setInterval(() => {
      msgIdx = (msgIdx + 1) % statusMessages.length;
      liveStatusText.textContent = statusMessages[msgIdx];
    }, 2000);

    // Initial step 1 Active
    setStepState(pipeStep1, pipeStep1Tag, 'active');

    // Smooth visual progression
    progressStepTimer = setTimeout(() => {
      setStepState(pipeStep1, pipeStep1Tag, 'complete');
      pipeConn1.className = 'step-connector complete';
      setStepState(pipeStep2, pipeStep2Tag, 'active');

      progressStepTimer = setTimeout(() => {
        setStepState(pipeStep2, pipeStep2Tag, 'complete');
        pipeConn2.className = 'step-connector complete';
        setStepState(pipeStep3, pipeStep3Tag, 'active');
      }, 3500);
    }, 2500);
  }

  function finalizePipelineSuccess() {
    if (statusInterval) clearInterval(statusInterval);
    if (progressStepTimer) clearTimeout(progressStepTimer);

    setStepState(pipeStep1, pipeStep1Tag, 'complete');
    pipeConn1.className = 'step-connector complete';
    setStepState(pipeStep2, pipeStep2Tag, 'complete');
    pipeConn2.className = 'step-connector complete';
    setStepState(pipeStep3, pipeStep3Tag, 'complete');
    liveStatusText.textContent = "Verification verified & completed!";
  }

  function finalizePipelineFailure(stage) {
    if (statusInterval) clearInterval(statusInterval);
    if (progressStepTimer) clearTimeout(progressStepTimer);

    if (stage === 'face') {
      setStepState(pipeStep1, pipeStep1Tag, 'failed');
      setStepState(pipeStep2, pipeStep2Tag, 'waiting');
      setStepState(pipeStep3, pipeStep3Tag, 'waiting');
    } else if (stage === 'search') {
      setStepState(pipeStep1, pipeStep1Tag, 'complete');
      pipeConn1.className = 'step-connector complete';
      setStepState(pipeStep2, pipeStep2Tag, 'failed');
      setStepState(pipeStep3, pipeStep3Tag, 'waiting');
    } else {
      setStepState(pipeStep1, pipeStep1Tag, 'complete');
      pipeConn1.className = 'step-connector complete';
      setStepState(pipeStep2, pipeStep2Tag, 'complete');
      pipeConn2.className = 'step-connector complete';
      setStepState(pipeStep3, pipeStep3Tag, 'failed');
    }
  }

  // ---------------------------------------------------------------------------
  // Form Submission & Verification Execution
  // ---------------------------------------------------------------------------
  verifyForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentSelectedFile) {
      alert('Please select or drop an image file first.');
      return;
    }

    // Prepare UI for request
    btnVerify.setAttribute('disabled', 'true');
    resultsDashboard.classList.add('hidden');
    errorCard.classList.add('hidden');
    startPipelineAnimation();

    const formData = new FormData();
    formData.append('image', currentSelectedFile);

    try {
      const response = await fetch('/api/verify', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Successful verification
        finalizePipelineSuccess();

        setTimeout(() => {
          pipelineProgressCard.classList.add('hidden');
          renderResults(data);
          btnVerify.removeAttribute('disabled');
        }, 800);

      } else {
        // Pipeline Stage Failure
        const failedStage = data.stage || 'server';
        finalizePipelineFailure(failedStage);

        setTimeout(() => {
          pipelineProgressCard.classList.add('hidden');
          renderError(failedStage, data.message || 'Pipeline verification could not be completed.');
          btnVerify.removeAttribute('disabled');
        }, 800);
      }

    } catch (networkErr) {
      console.error('Network or request error:', networkErr);
      finalizePipelineFailure('server');
      setTimeout(() => {
        pipelineProgressCard.classList.add('hidden');
        renderError('server', 'Failed to communicate with verification backend. Please check the server connection.');
        btnVerify.removeAttribute('disabled');
      }, 800);
    }
  });

  // ---------------------------------------------------------------------------
  // Render Results Dashboard
  // ---------------------------------------------------------------------------
  function renderResults(data) {
    // Stage 1 Face Data
    resFaceDim.textContent = data.face?.embedding_dim || 128;

    // Stage 2 Search Data
    resTotalMatches.textContent = data.search?.matches_found || 0;
    resSocialMatches.textContent = data.search?.social_matches_found || 0;

    const bestMatch = data.search?.best_match || {};
    const platform = bestMatch.platform || 'Web';
    resPlatformBadge.textContent = platform;
    resPlatformBadge.className = `platform-badge ${getPlatformClass(platform)}`;

    resMatchTitle.textContent = bestMatch.title || 'Discovered Profile Match';
    resMatchSource.textContent = bestMatch.source || platform;
    resMatchRank.textContent = `#${bestMatch.position || 1}`;

    if (bestMatch.link) {
      resMatchLink.href = bestMatch.link;
      resMatchLink.classList.remove('hidden');
    } else {
      resMatchLink.classList.add('hidden');
    }

    // Stage 3 Blockchain Data
    currentFullHash = data.blockchain?.post_hash || '';
    resRecordHashShort.textContent = shortenHash(currentFullHash, 16, 12);
    resBlockIndex.textContent = `#${data.blockchain?.block_index ?? 0}`;
    resBlockHash.textContent = shortenHash(data.blockchain?.block_hash || '0000', 8, 6);
    resChainLength.textContent = `Total Blocks: ${data.blockchain?.total_chain_blocks || ((data.blockchain?.block_index ?? 0) + 1)}`;

    // Show Results Dashboard
    resultsDashboard.classList.remove('hidden');
    resultsDashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---------------------------------------------------------------------------
  // Render Error UI
  // ---------------------------------------------------------------------------
  function renderError(stage, message) {
    const stageTitles = {
      'face': 'Face Detection Failed',
      'search': 'Web Search Failed',
      'blockchain': 'Blockchain Verification Failed',
      'upload': 'File Upload Error',
      'server': 'Server Error'
    };

    errorStageBadge.textContent = `Stage: ${stage.toUpperCase()}`;
    errorHeading.textContent = stageTitles[stage] || 'Verification Failed';
    errorMessage.textContent = message;

    errorCard.classList.remove('hidden');
    errorCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---------------------------------------------------------------------------
  // Copy Full SHA-256 Hash to Clipboard
  // ---------------------------------------------------------------------------
  btnCopyHash.addEventListener('click', async () => {
    if (!currentFullHash) return;

    try {
      await navigator.clipboard.writeText(currentFullHash);
      copyBtnText.textContent = 'COPIED!';
      showToast('SHA-256 record hash copied to clipboard!');
      setTimeout(() => {
        copyBtnText.textContent = 'COPY';
      }, 2000);
    } catch (err) {
      console.warn('Clipboard API error, fallback to execCommand:', err);
      const textArea = document.createElement('textarea');
      textArea.value = currentFullHash;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      copyBtnText.textContent = 'COPIED!';
      showToast('SHA-256 record hash copied to clipboard!');
      setTimeout(() => {
        copyBtnText.textContent = 'COPY';
      }, 2000);
    }
  });

  // ---------------------------------------------------------------------------
  // Reset Application State Without Reloading
  // ---------------------------------------------------------------------------
  function resetApplicationState() {
    currentSelectedFile = null;
    currentFullHash = '';
    fileInput.value = '';
    imagePreview.src = '';
    previewFilename.textContent = '-';
    previewFilesize.textContent = '-';

    previewContainer.classList.add('hidden');
    dropPrompt.classList.remove('hidden');
    btnVerify.setAttribute('disabled', 'true');

    resultsDashboard.classList.add('hidden');
    errorCard.classList.add('hidden');
    pipelineProgressCard.classList.add('hidden');
    resetPipelineSteps();

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  btnResetDashboard.addEventListener('click', resetApplicationState);
  btnTryAnother.addEventListener('click', resetApplicationState);
});
