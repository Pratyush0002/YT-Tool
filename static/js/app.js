// State
let currentVideoFile = null;
let currentData = null;
let hasApiKey = false;
let isYouTubeConnected = false;
let connectedChannelData = null;

// DOM Elements
const dropZone = document.getElementById('dropZone');
const videoFileInput = document.getElementById('videoFileInput');
const dropZonePrompt = document.getElementById('dropZonePrompt');
const videoPreviewBox = document.getElementById('videoPreviewBox');
const previewPlayer = document.getElementById('previewPlayer');
const previewFileName = document.getElementById('previewFileName');
const removeVideoBtn = document.getElementById('removeVideoBtn');

const autoUploadToggle = document.getElementById('autoUploadToggle');
const privacyBox = document.getElementById('privacyBox');
const actionBtnText = document.getElementById('actionBtnText');
const generateBtn = document.getElementById('generateBtn');

const categorySelect = document.getElementById('categorySelect');
const styleSelect = document.getElementById('styleSelect');
const langSelect = document.getElementById('langSelect');
const notesInput = document.getElementById('notesInput');

const progressContainer = document.getElementById('progressContainer');
const progressBarFill = document.getElementById('progressBarFill');
const progressStatusText = document.getElementById('progressStatusText');

const stage1 = document.getElementById('stage1');
const stage2 = document.getElementById('stage2');
const stage3 = document.getElementById('stage3');
const stage4 = document.getElementById('stage4');

const emptyState = document.getElementById('emptyState');
const resultsWrapper = document.getElementById('resultsWrapper');
const ytLiveSuccessCard = document.getElementById('ytLiveSuccessCard');
const ytConnectPromptCard = document.getElementById('ytConnectPromptCard');
const detectedCatName = document.getElementById('detectedCatName');
const detectedCatReason = document.getElementById('detectedCatReason');
const ytSuccessCategory = document.getElementById('ytSuccessCategory');
const bestTitleText = document.getElementById('bestTitleText');

// YouTube Modals & Controls
const ytChannelBtn = document.getElementById('ytChannelBtn');
const ytChannelStatusText = document.getElementById('ytChannelStatusText');
const ytConnectModal = document.getElementById('ytConnectModal');
const ytConnectedState = document.getElementById('ytConnectedState');
const ytDisconnectedState = document.getElementById('ytDisconnectedState');
const connectedChannelThumb = document.getElementById('connectedChannelThumb');
const connectedChannelTitle = document.getElementById('connectedChannelTitle');
const connectedChannelSubs = document.getElementById('connectedChannelSubs');
const connectedChannelVideos = document.getElementById('connectedChannelVideos');
const disconnectYtBtn = document.getElementById('disconnectYtBtn');
const ytClientIdInput = document.getElementById('ytClientIdInput');
const ytClientSecretInput = document.getElementById('ytClientSecretInput');
const saveYtConfigBtn = document.getElementById('saveYtConfigBtn');

// Modals
const settingsModal = document.getElementById('settingsModal');
const historyModal = document.getElementById('historyModal');
const settingsBtn = document.getElementById('settingsBtn');
const historyBtn = document.getElementById('historyBtn');
const apiKeyInput = document.getElementById('apiKeyInput');
const saveApiKeyBtn = document.getElementById('saveApiKeyBtn');
const keyStatusText = document.getElementById('keyStatusText');
const historyListContainer = document.getElementById('historyListContainer');

// Action Buttons
const copyAllBtn = document.getElementById('copyAllBtn');
const downloadTxtBtn = document.getElementById('downloadTxtBtn');
const copyTagsStringBtn = document.getElementById('copyTagsStringBtn');
const ytLiveShortsLinkBtn = document.getElementById('ytLiveShortsLinkBtn');
const copyLiveShortsUrlBtn = document.getElementById('copyLiveShortsUrlBtn');

let liveShortsUrl = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkApiKeyStatus();
    checkYouTubeStatus();
    setupDropZone();
    setupEventHandlers();
    checkUrlParams();
});

// ----------------- Check URL Query Params ----------------- //
function checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('youtube_connected') === 'true') {
        showToast('🎉 आपका YouTube चैनल सफलतापूर्वक कनेक्ट हो गया!');
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (params.get('youtube_error')) {
        showToast('❌ YouTube कनेक्शन त्रुटि: ' + params.get('youtube_error'));
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// ----------------- Check API Key Status ----------------- //
async function checkApiKeyStatus() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        if (data.hasKey) {
            hasApiKey = true;
            keyStatusText.textContent = `🔑 Key: ${data.maskedKey}`;
        } else {
            hasApiKey = false;
            keyStatusText.textContent = 'AI Key सेट करें';
        }
    } catch (err) {
        console.error('Error fetching key status:', err);
    }
}

// ----------------- Check YouTube Status ----------------- //
async function checkYouTubeStatus() {
    try {
        const res = await fetch('/api/youtube/status');
        const data = await res.json();
        isYouTubeConnected = data.connected;

        if (data.connected && data.channel) {
            connectedChannelData = data.channel;
            ytChannelStatusText.textContent = `🔴 ${data.channel.title || 'Connected'}`;
            ytChannelBtn.classList.add('connected');

            ytConnectedState.style.display = 'block';
            ytDisconnectedState.style.display = 'none';

            connectedChannelTitle.textContent = data.channel.title || 'My Channel';
            connectedChannelSubs.textContent = formatCount(data.channel.subscriberCount || 0);
            connectedChannelVideos.textContent = formatCount(data.channel.videoCount || 0);
            if (data.channel.thumbnail) {
                connectedChannelThumb.src = data.channel.thumbnail;
                connectedChannelThumb.style.display = 'block';
            } else {
                connectedChannelThumb.style.display = 'none';
            }
        } else {
            connectedChannelData = null;
            ytChannelStatusText.textContent = 'YouTube चैनल जोड़ें';
            ytChannelBtn.classList.remove('connected');

            ytConnectedState.style.display = 'none';
            ytDisconnectedState.style.display = 'block';
        }
    } catch (err) {
        console.error('Error fetching YouTube status:', err);
    }
}

function formatCount(num) {
    num = parseInt(num) || 0;
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
}

// ----------------- Drop Zone & Video Preview ----------------- //
function setupDropZone() {
    dropZone.addEventListener('click', (e) => {
        if (e.target !== removeVideoBtn) {
            videoFileInput.click();
        }
    });

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
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    videoFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    removeVideoBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearSelectedFile();
    });

    autoUploadToggle.addEventListener('change', () => {
        if (autoUploadToggle.checked) {
            privacyBox.style.display = 'block';
            actionBtnText.textContent = 'ऑटो-प्रोसेस और यूट्यूब पर अपलोड करें (1-Click)';
        } else {
            privacyBox.style.display = 'none';
            actionBtnText.textContent = '⚡ सिर्फ वायरल टाइटल & टैग्स तैयार करें';
        }
    });
}

function handleSelectedFile(file) {
    if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|mov|webm|avi|mkv)$/i)) {
        showToast('⚠️ कृपया मान्य वीडियो फ़ाइल चुनें (.mp4, .mov, .webm)');
        return;
    }

    if (file.size > 150 * 1024 * 1024) {
        showToast('⚠️ फ़ाइल का आकार 150MB से कम होना चाहिए');
        return;
    }

    currentVideoFile = file;
    previewFileName.textContent = file.name;

    const fileUrl = URL.createObjectURL(file);
    previewPlayer.src = fileUrl;

    dropZonePrompt.style.display = 'none';
    videoPreviewBox.style.display = 'flex';
    showToast('✅ वीडियो लोड हो गया! अब बस बटन दबाएं।');
}

function clearSelectedFile() {
    currentVideoFile = null;
    videoFileInput.value = '';
    previewPlayer.pause();
    previewPlayer.src = '';
    dropZonePrompt.style.display = 'block';
    videoPreviewBox.style.display = 'none';
}

// ----------------- Event Handlers ----------------- //
function setupEventHandlers() {
    generateBtn.addEventListener('click', startAutoPublishPipeline);

    ytChannelBtn.addEventListener('click', () => openModal('ytConnectModal'));
    settingsBtn.addEventListener('click', () => openModal('settingsModal'));
    historyBtn.addEventListener('click', () => {
        loadHistoryList();
        openModal('historyModal');
    });

    saveApiKeyBtn.addEventListener('click', saveApiKey);
    saveYtConfigBtn.addEventListener('click', saveYouTubeConfigAndAuth);
    disconnectYtBtn.addEventListener('click', disconnectYouTubeAccount);

    copyAllBtn.addEventListener('click', copyAllContent);
    downloadTxtBtn.addEventListener('click', downloadAsTxt);
    copyTagsStringBtn.addEventListener('click', () => copyElementText('tagsStringText'));

    copyLiveShortsUrlBtn.addEventListener('click', () => {
        if (liveShortsUrl) {
            copyText(liveShortsUrl);
        }
    });
}

// ----------------- The Zero-Effort Pipeline ----------------- //
function startAutoPublishPipeline() {
    if (!currentVideoFile) {
        showToast('⚠️ कृपया पहले अपनी वीडियो फ़ाइल डालें!');
        return;
    }

    const isAuto = autoUploadToggle.checked;
    const privacy = document.querySelector('input[name="privacyStatus"]:checked')?.value || 'public';
    const chosenCategory = categorySelect ? categorySelect.value : 'auto';

    setStepperStage(1, 15, 'स्टेज 1: वीडियो अपलोड हो रहा है...');

    const formData = new FormData();
    formData.append('video', currentVideoFile);
    formData.append('category', chosenCategory);
    formData.append('style', styleSelect.value);
    formData.append('language', langSelect.value);
    formData.append('viralStrategy', 'max_retention');
    formData.append('notes', notesInput.value.trim());
    formData.append('autoUpload', isAuto ? 'true' : 'false');
    formData.append('privacyStatus', privacy);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/analyze-video', true);

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 40);
            progressBarFill.style.width = `${Math.max(15, pct)}%`;
            if (pct >= 35) {
                setStepperStage(2, 50, 'स्टेज 2: AI वीडियो देखकर सही कैटेगरी, वायरल टाइटल & टैग्स निर्धारित कर रहा है...');
            }
        }
    };

    xhr.onload = () => {
        if (isAuto && isYouTubeConnected) {
            setStepperStage(3, 85, 'स्टेज 3: वीडियो के अनुसार चुनी गई कैटेगरी में YouTube पर पब्लिश हो रहा है...');
        } else {
            setStepperStage(2, 90, 'फ़ाइनल वायरल फॉर्मेटिंग हो रही है...');
        }

        setTimeout(() => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success && response.data) {
                        setStepperStage(4, 100, '🎉 बधाई हो! काम पूरा हो गया!');
                        setTimeout(() => {
                            setStepperProgress(false);
                            displayResults(response.data, response.youtube);
                        }, 600);
                    } else {
                        setStepperProgress(false);
                        showToast('❌ त्रुटि: ' + (response.error || 'अज्ञात त्रुटि'));
                    }
                } catch (err) {
                    setStepperProgress(false);
                    showToast('❌ रिस्पॉन्स प्रोसेस करने में समस्या');
                }
            } else {
                setStepperProgress(false);
                showToast('❌ सर्वर एरर (' + xhr.status + ')');
            }
        }, 800);
    };

    xhr.onerror = () => {
        setStepperProgress(false);
        showToast('❌ नेटवर्क या सर्वर से कनेक्शन में समस्या');
    };

    xhr.send(formData);
}

function setStepperProgress(show) {
    if (show) {
        progressContainer.style.display = 'block';
        generateBtn.disabled = true;
    } else {
        progressContainer.style.display = 'none';
        generateBtn.disabled = false;
    }
}

function setStepperStage(stageNum, pct, text) {
    setStepperProgress(true);
    progressBarFill.style.width = `${pct}%`;
    progressStatusText.textContent = text;

    [stage1, stage2, stage3, stage4].forEach((el, idx) => {
        if (idx + 1 < stageNum) {
            el.className = 'stage-step done';
        } else if (idx + 1 === stageNum) {
            el.className = 'stage-step active';
        } else {
            el.className = 'stage-step';
        }
    });
}

// ----------------- Display Results ----------------- //
function displayResults(data, youtubeResult) {
    currentData = data;
    emptyState.style.display = 'none';
    resultsWrapper.style.display = 'flex';

    resultsWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // 1. Detected Category Banner
    const catName = data.category_name || 'Comedy (23)';
    const catReason = data.category_reason || 'AI ने वीडियो के कंटेंट और विजुअल्स के अनुसार यह कैटेगरी निर्धारित की है।';
    if (detectedCatName) detectedCatName.textContent = catName;
    if (detectedCatReason) detectedCatReason.textContent = catReason;

    // 2. YouTube Live Upload Success Banner
    if (youtubeResult && youtubeResult.success) {
        ytLiveSuccessCard.style.display = 'flex';
        ytConnectPromptCard.style.display = 'none';

        document.getElementById('ytUploadedTitle').textContent = youtubeResult.title || data.best_title;
        document.getElementById('ytSuccessChannelName').textContent = connectedChannelData ? connectedChannelData.title : 'My YouTube Channel';
        document.getElementById('ytSuccessPrivacy').textContent = (youtubeResult.privacy || 'PUBLIC').toUpperCase();
        if (ytSuccessCategory) ytSuccessCategory.textContent = youtubeResult.category_name || catName;

        liveShortsUrl = youtubeResult.short_url || `https://youtube.com/shorts/${youtubeResult.video_id}`;
        ytLiveShortsLinkBtn.href = liveShortsUrl;
        showToast('🎉 आपका वीडियो सही कैटेगरी के साथ सीधे YouTube चैनल पर लाइव हो गया!');
    } else {
        ytLiveSuccessCard.style.display = 'none';
        if (!isYouTubeConnected && autoUploadToggle.checked) {
            ytConnectPromptCard.style.display = 'flex';
        } else {
            ytConnectPromptCard.style.display = 'none';
        }
    }

    // 3. Best Title Display
    const bestTitle = data.best_title || (data.titles ? data.titles[0].title : 'Short Video');
    bestTitleText.textContent = bestTitle;

    // 4. Viral Score
    const score = data.viral_score || 98;
    document.getElementById('viralScoreNum').textContent = score;
    const mb = data.metrics_breakdown || {};
    document.getElementById('metricCtr').textContent = mb.ctr_potential || '99% (इमोजी हुक)';
    document.getElementById('metricRetention').textContent = mb.retention_power || '97% (सस्पेंस)';
    document.getElementById('metricShare').textContent = mb.shareability || '98% (देसी रिलेट)';
    document.getElementById('metricSeo').textContent = mb.algorithm_seo || '100% (स्टूडियो रेडी)';

    // 5. Summary & Hook
    document.getElementById('summaryText').textContent = data.summary || 'वीडियो का सटीक विश्लेषण।';
    document.getElementById('hookReasonText').textContent = data.hook_analysis || 'पहले 2-3 सेकंड का ट्विस्ट दर्शक को पूरा देखने पर मजबूर करेगा।';
    document.getElementById('loopHackText').textContent = data.loop_hack || 'वीडियो के अंतिम सेकंड को पहले सेकंड से जोड़ें ताकि वीडियो लूप में 120%+ बार देखा जाए!';

    // 6. Alternate Titles
    const titlesList = document.getElementById('titlesList');
    titlesList.innerHTML = '';
    if (data.titles && Array.isArray(data.titles)) {
        data.titles.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'title-card';
            card.innerHTML = `
                <div class="title-main-info">
                    <div class="title-tags-row">
                        <span class="title-type-badge">${escapeHtml(item.type || `टाइटल ${index + 1}`)}</span>
                        <span class="ctr-badge">🔥 ${item.ctr_score || 98}% Viral Potential</span>
                    </div>
                    <div class="title-text" onclick="copyText('${escapeQuotes(item.title)}')">${escapeHtml(item.title)}</div>
                    <div class="title-reason">💡 ${escapeHtml(item.hook_reason || '')}</div>
                </div>
                <button class="btn-copy-card" onclick="copyText('${escapeQuotes(item.title)}')">📋 कॉपी</button>
            `;
            titlesList.appendChild(card);
        });
    }

    // 7. Description
    const descText = data.description || '';
    document.getElementById('descriptionText').textContent = descText;

    // 8. Tags & Tags String
    const tagsString = data.tags_string || (data.tags ? data.tags.join(', ') : '');
    document.getElementById('tagsStringText').textContent = tagsString;

    const charCount = tagsString.length;
    const counterEl = document.getElementById('tagsCharCount');
    counterEl.textContent = `${charCount} / 500 अक्षर`;
    if (charCount > 500) {
        counterEl.style.color = '#ff476f';
    } else {
        counterEl.style.color = 'var(--accent-green)';
    }

    // Tag pills
    const tagPills = document.getElementById('tagPills');
    tagPills.innerHTML = '';
    if (data.tags && Array.isArray(data.tags)) {
        data.tags.forEach(tag => {
            const pill = document.createElement('span');
            pill.className = 'tag-pill';
            pill.innerHTML = `<span>${escapeHtml(tag)}</span><span class="pill-copy">📋</span>`;
            pill.onclick = () => copyText(tag);
            tagPills.appendChild(pill);
        });
    }

    // 9. Hashtags
    const hashtagsList = document.getElementById('hashtagsList');
    hashtagsList.innerHTML = '';
    if (data.hashtags && Array.isArray(data.hashtags)) {
        data.hashtags.forEach(tag => {
            const hPill = document.createElement('span');
            hPill.className = 'hashtag-pill';
            hPill.textContent = tag.startsWith('#') ? tag : '#' + tag;
            hPill.onclick = () => copyText(hPill.textContent);
            hashtagsList.appendChild(hPill);
        });
    }
}

// ----------------- YouTube OAuth Setup ----------------- //
async function saveYouTubeConfigAndAuth() {
    const clientId = ytClientIdInput.value.trim();
    const clientSecret = ytClientSecretInput.value.trim();

    if (!clientId || !clientSecret) {
        showToast('⚠️ कृपया Client ID और Client Secret दोनों दर्ज करें!');
        return;
    }

    try {
        const res = await fetch('/api/youtube/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientId, clientSecret })
        });
        const data = await res.json();
        if (data.success) {
            const authRes = await fetch('/api/youtube/auth-url');
            const authData = await authRes.json();
            if (authData.success && authData.authUrl) {
                window.location.href = authData.authUrl;
            } else {
                showToast('❌ OAuth URL जनरेट करने में त्रुटि: ' + (authData.error || ''));
            }
        } else {
            showToast('❌ त्रुटि: ' + (data.error || 'सेव नहीं हो सका'));
        }
    } catch (err) {
        showToast('❌ सर्वर से कनेक्शन में समस्या');
    }
}

async function disconnectYouTubeAccount() {
    if (!confirm('क्या आप सचमुच अपना YouTube चैनल डिस्कनेक्ट करना चाहते हैं?')) return;
    try {
        const res = await fetch('/api/youtube/disconnect', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            checkYouTubeStatus();
            showToast('🚪 YouTube चैनल डिस्कनेक्ट हो गया');
        }
    } catch (err) {
        showToast('❌ डिस्कनेक्ट नहीं हो सका');
    }
}

// ----------------- Save API Key ----------------- //
async function saveApiKey() {
    const key = apiKeyInput.value.trim();
    if (!key) {
        showToast('⚠️ कृपया API Key दर्ज करें');
        return;
    }

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apiKey: key })
        });
        const data = await res.json();
        if (data.success) {
            hasApiKey = true;
            keyStatusText.textContent = `🔑 Key: ${data.maskedKey}`;
            apiKeyInput.value = '';
            closeModal('settingsModal');
            showToast('✅ API Key सफलतापूर्वक सेव हो गई!');
        } else {
            showToast('❌ त्रुटि: ' + (data.error || 'सेव नहीं हो सकी'));
        }
    } catch (err) {
        showToast('❌ सर्वर से कनेक्शन एरर');
    }
}

function togglePasswordVisibility() {
    const type = apiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
    apiKeyInput.setAttribute('type', type);
}

// ----------------- Copy & Export Utilities ----------------- //
function copyText(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast('📋 कॉपी हो गया: ' + (text.length > 30 ? text.substring(0, 30) + '...' : text));
    }).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('📋 कॉपी हो गया!');
    });
}

function copyElementText(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        copyText(el.innerText || el.textContent);
    }
}

function copyAllContent() {
    if (!currentData) return;
    
    let content = `=====================================\n`;
    content += `🎬 YOUTUBE SHORTS VIRAL PACKAGE\n`;
    content += `=====================================\n\n`;

    content += `🏷️ CATEGORY: ${currentData.category_name || 'Comedy'}\n\n`;
    content += `🏆 BEST TITLE:\n${currentData.best_title}\n\n`;
    content += `📝 DESCRIPTION:\n${currentData.description}\n\n`;
    content += `🏷️ TAGS:\n${currentData.tags_string}\n\n`;
    content += `📌 PINNED COMMENT:\n${currentData.pinned_comment}\n\n`;
    content += `🌀 LOOP HACK: ${currentData.loop_hack || ''}\n`;
    content += `🕒 BEST UPLOAD TIME: ${currentData.best_time_to_post}\n`;

    copyText(content);
    showToast('📋 पूरा पैकेज एक साथ कॉपी हो गया!');
}

function downloadAsTxt() {
    if (!currentData) return;

    let content = `=====================================\n`;
    content += `🎬 YOUTUBE SHORTS VIRAL PACKAGE\n`;
    content += `Date: ${new Date().toLocaleString()}\n`;
    content += `=====================================\n\n`;

    content += `🏷️ CATEGORY: ${currentData.category_name || 'Comedy'}\n\n`;
    content += `🏆 BEST TITLE:\n${currentData.best_title}\n\n`;
    content += `📝 DESCRIPTION:\n${currentData.description}\n\n`;
    content += `🏷️ TAGS:\n${currentData.tags_string}\n\n`;
    content += `📌 PINNED COMMENT:\n${currentData.pinned_comment}\n\n`;
    content += `🌀 LOOP HACK:\n${currentData.loop_hack || ''}\n\n`;
    content += `🕒 BEST TIME: ${currentData.best_time_to_post}\n`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `shorts_viral_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('📥 .TXT फ़ाइल डाउनलोड हो गई!');
}

// ----------------- History ----------------- //
async function loadHistoryList() {
    historyListContainer.innerHTML = '<div style="text-align:center; padding: 1rem; color: #888;">लोड हो रहा है...</div>';
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        if (data.success && data.history && data.history.length > 0) {
            historyListContainer.innerHTML = '';
            data.history.forEach(item => {
                const row = document.createElement('div');
                row.className = 'history-item';
                row.innerHTML = `
                    <div class="history-info">
                        <div class="history-title">${escapeHtml(item.primary_title || item.filename)}</div>
                        <div class="history-meta">
                            <span>📅 ${escapeHtml(item.date_display || '')}</span>
                            <span>🏷️ ${escapeHtml(item.category || 'Comedy')}</span>
                            ${item.youtube_url ? '<span style="color:#00e676">📺 YouTube Live</span>' : ''}
                        </div>
                    </div>
                    <div class="history-actions">
                        ${item.youtube_url ? `<a href="${item.youtube_url}" target="_blank" class="btn btn-sm btn-primary" style="padding:0.25rem 0.6rem;">देखें ↗</a>` : ''}
                        <button class="btn btn-sm btn-outline" onclick="loadHistoryItem('${item.id}')">खोलें</button>
                    </div>
                `;
                historyListContainer.appendChild(row);
            });
        } else {
            historyListContainer.innerHTML = '<div style="text-align:center; padding: 2rem; color: #777;">कोई पिछला रिकॉर्ड नहीं है।</div>';
        }
    } catch (err) {
        historyListContainer.innerHTML = '<div style="text-align:center; padding: 1rem; color: #f44;">इतिहास लोड करने में त्रुटि।</div>';
    }
}

window.loadHistoryItem = async function(id) {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const found = data.history.find(h => h.id === id);
        if (found && found.result) {
            closeModal('historyModal');
            displayResults(found.result, found.result.youtube_published);
            showToast('📂 पिछला रिकॉर्ड लोड हो गया!');
        }
    } catch (err) {
        showToast('❌ लोड नहीं हो सका');
    }
};

// ----------------- Modal Controls ----------------- //
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// ----------------- Toast Notification ----------------- //
let toastTimer = null;
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 3200);
}

// ----------------- Helpers ----------------- //
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeQuotes(str) {
    if (!str) return '';
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
