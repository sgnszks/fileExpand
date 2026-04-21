/**
 * @fileoverview 文件体积膨胀工具 - 前端交互逻辑
 *
 * 处理文件上传、倍数输入、进度展示、结果下载等交互。
 */

(function () {
    'use strict';

    /** @type {File|null} */
    let selectedFile = null;

    /** @type {number|null} */
    let selectedMultiplier = null;

    /** @type {boolean} */
    let isProcessing = false;

    /* ===== DOM 元素引用 ===== */

    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const removeFileBtn = document.getElementById('removeFile');
    const multiplierInput = document.getElementById('multiplierInput');
    const presetButtons = document.querySelectorAll('.btn-preset');
    const processBtn = document.getElementById('processBtn');
    const btnText = processBtn.querySelector('.btn-text');
    const btnLoading = processBtn.querySelector('.btn-loading');
    const statusSection = document.getElementById('statusSection');
    const resultSection = document.getElementById('resultSection');
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    const downloadBtn = document.getElementById('downloadBtn');

    /* ===== 文件选择与拖拽 ===== */

    fileInput.addEventListener('change', handleFileSelect);
    removeFileBtn.addEventListener('click', removeFile);

    uploadArea.addEventListener('dragover', function (e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function () {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function (e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });

    /**
     * @description 处理文件选择事件
     */
    function handleFileSelect() {
        const file = fileInput.files[0];
        if (!file) return;

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatSize(file.size);
        fileInfo.style.display = 'flex';
        hideError();
        hideResult();
        updateProcessButton();
    }

    /**
     * @description 移除已选择的文件
     */
    function removeFile() {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        updateProcessButton();
    }

    /* ===== 倍数输入 ===== */

    presetButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            presetButtons.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
            selectedMultiplier = parseFloat(btn.dataset.value);
            multiplierInput.value = selectedMultiplier;
            updateProcessButton();
        });
    });

    multiplierInput.addEventListener('input', function () {
        const val = parseFloat(multiplierInput.value);
        presetButtons.forEach(function (b) {
            b.classList.toggle('active', parseFloat(b.dataset.value) === val);
        });
        selectedMultiplier = isNaN(val) ? null : val;
        updateProcessButton();
    });

    /* ===== 按钮状态 ===== */

    /**
     * @description 更新处理按钮的可用状态
     */
    function updateProcessButton() {
        const canProcess = selectedFile !== null
            && selectedMultiplier !== null
            && selectedMultiplier >= 1.1
            && selectedMultiplier <= 10
            && !isProcessing;
        processBtn.disabled = !canProcess;
    }

    /* ===== 处理流程 ===== */

    processBtn.addEventListener('click', startProcessing);

    /**
     * @description 启动文件处理流程
     */
    async function startProcessing() {
        if (!selectedFile || !selectedMultiplier || isProcessing) return;

        isProcessing = true;
        updateProcessButton();
        setBtnLoading(true);
        hideError();
        hideResult();
        showStatus();

        try {
            setStep('upload', 'active');

            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('multiplier', selectedMultiplier.toString());

            setStep('upload', 'completed');
            setStep('validate', 'active');

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            setStep('validate', 'completed');
            setStep('process', 'active');

            const data = await response.json();

            if (data.success) {
                setStep('process', 'completed');
                setStep('verify', 'active');

                await sleep(300);

                setStep('verify', 'completed');
                setStep('done', 'completed');

                showResult(data.data);
            } else {
                setAllStepsError();
                showError(data.error || '处理失败，请重试');
            }
        } catch (err) {
            setAllStepsError();
            showError('网络请求失败，请检查网络连接后重试');
        } finally {
            isProcessing = false;
            updateProcessButton();
            setBtnLoading(false);
        }
    }

    /* ===== 状态步骤 ===== */

    /**
     * @description 显示状态栏
     */
    function showStatus() {
        statusSection.style.display = 'block';
        document.querySelectorAll('.status-step').forEach(function (step) {
            step.className = 'status-step';
        });
    }

    /**
     * @description 设置指定步骤的状态
     * @param {string} stepName - 步骤名称
     * @param {string} state - 状态 ('active'|'completed'|'error')
     */
    function setStep(stepName, state) {
        const step = document.querySelector(`.status-step[data-step="${stepName}"]`);
        if (step) {
            step.className = 'status-step ' + state;
        }
    }

    /**
     * @description 将所有步骤标记为错误状态
     */
    function setAllStepsError() {
        document.querySelectorAll('.status-step').forEach(function (step) {
            if (step.classList.contains('active')) {
                step.className = 'status-step error';
            }
        });
    }

    /* ===== 结果展示 ===== */

    /**
     * @description 显示处理结果
     * @param {Object} data - 后端返回的处理结果数据
     */
    function showResult(data) {
        document.getElementById('resultOriginalSize').textContent = formatSize(data.original_size);
        document.getElementById('resultOutputSize').textContent = formatSize(data.output_size);
        document.getElementById('resultTargetMultiplier').textContent = data.target_multiplier + 'x';
        document.getElementById('resultActualMultiplier').textContent = data.actual_multiplier + 'x';

        var strategyMap = {
            'custom_xml_metadata': '自定义 XML 元数据注入',
            'repack_low_compression': '低压缩率重新打包',
            'combined_metadata_and_repack': '元数据注入 + 低压缩率重新打包',
            'pdf_metadata_stream': 'PDF 元数据流注入',
        };
        var strategyText = strategyMap[data.strategy_used] || data.strategy_used;
        document.getElementById('resultStrategy').textContent = strategyText;

        if (data.warnings && data.warnings.length > 0) {
            var warningsList = document.getElementById('warningsList');
            warningsList.innerHTML = '';
            data.warnings.forEach(function (w) {
                var li = document.createElement('li');
                li.textContent = w;
                warningsList.appendChild(li);
            });
            document.getElementById('warningsArea').style.display = 'block';
        } else {
            document.getElementById('warningsArea').style.display = 'none';
        }

        downloadBtn.href = '/api/download/' + encodeURIComponent(data.output_filename);
        resultSection.style.display = 'block';
    }

    /**
     * @description 隐藏结果区域
     */
    function hideResult() {
        resultSection.style.display = 'none';
    }

    /* ===== 错误展示 ===== */

    /**
     * @description 显示错误信息
     * @param {string} msg - 错误描述
     */
    function showError(msg) {
        errorMessage.textContent = msg;
        errorSection.style.display = 'block';
    }

    /**
     * @description 隐藏错误区域
     */
    function hideError() {
        errorSection.style.display = 'none';
    }

    /* ===== 工具函数 ===== */

    /**
     * @description 切换处理按钮的加载状态
     * @param {boolean} loading - 是否处于加载中
     */
    function setBtnLoading(loading) {
        btnText.style.display = loading ? 'none' : 'inline';
        btnLoading.style.display = loading ? 'inline-flex' : 'none';
    }

    /**
     * @description 格式化文件大小为可读字符串
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的大小描述
     */
    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        var units = ['B', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(1024));
        i = Math.min(i, units.length - 1);
        return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 2) + ' ' + units[i];
    }

    /**
     * @description 异步等待指定毫秒数
     * @param {number} ms - 毫秒数
     * @returns {Promise<void>}
     */
    function sleep(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

})();
