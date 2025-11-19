document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const keywordInput = document.getElementById('keywordInput');
    const combinationType = document.getElementById('combinationType');
    const combinationPosition = document.getElementById('combinationPosition');
    const combinationLength = document.getElementById('combinationLength');
    const generateButton = document.getElementById('generateButton');
    const queryButton = document.getElementById('queryButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const combinationsList = document.getElementById('combinationsList');
    const resultsContent = document.getElementById('resultsContent');
    const availableList = document.getElementById('availableList');
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // 创建错误提示元素
    let errorModal = null;
    
    // 存储生成的域名列表
    let generatedDomains = [];
    let queryResults = {};
    
    // 初始化选项卡切换
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有选项卡的活动状态
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 添加当前选项卡的活动状态
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // 生成组合按钮点击事件
    generateButton.addEventListener('click', function() {
        generateDomainCombinations();
    });
    
    // 批量查询按钮点击事件
    queryButton.addEventListener('click', function() {
        batchQueryDomains();
    });
    
    // 生成域名组合
    function generateDomainCombinations() {
        const keyword = keywordInput.value.trim();
        const type = combinationType.value;
        const length = parseInt(combinationLength.value);
        
        // 输入验证
        if (!keyword) {
            showError('请输入查询关键字');
            return;
        }
        
        if (!/^[a-zA-Z0-9-]+$/.test(keyword)) {
            showError('关键字只能包含字母、数字和连字符');
            return;
        }
        
        // 获取选中的后缀
        const selectedTLDs = [];
        const tldCheckboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]:checked');
        tldCheckboxes.forEach(checkbox => {
            selectedTLDs.push(checkbox.id);
        });
        
        if (selectedTLDs.length === 0) {
            showError('请至少选择一个域名后缀');
            return;
        }
        
        // 检查生成数量是否过大
        let estimatedCount = 1;
        if (type === 'number' || type === 'letter') {
            estimatedCount = Math.pow(type === 'number' ? 10 : 26, length);
        } else if (type === 'both') {
            estimatedCount = Math.pow(36, length);
        }
        
        // 获取组合位置
        const position = combinationPosition.value;
        let positionMultiplier = 1;
        if (position === 'both') {
            positionMultiplier = 2; // 前缀和后缀都要
        }
        
        // 考虑组合位置和多个后缀的情况
        const totalEstimated = estimatedCount * selectedTLDs.length * positionMultiplier;
        
        if (totalEstimated > 1000) {
            showError(`生成数量过大 (约${totalEstimated}个)，请减小组合长度`);
            return;
        }
        
        // 清空之前的结果
        generatedDomains = [];
        combinationsList.innerHTML = '';
        
        // 生成组合
        const combinations = generateCombinations(type, length);
        
        // 生成完整域名
        combinations.forEach(combination => {
            selectedTLDs.forEach(tld => {
                let domain;
                if (combination === '') {
                    // 不组合的情况
                    domain = `${keyword}.${tld}`;
                    generatedDomains.push(domain);
                } else {
                    // 根据组合位置生成域名
                    if (position === 'suffix' || position === 'both') {
                        // 生成关键字+组合的域名（后缀组合）
                        const suffixDomain = `${keyword}${combination}.${tld}`;
                        generatedDomains.push(suffixDomain);
                    }
                    
                    if (position === 'prefix' || position === 'both') {
                        // 生成组合+关键字的域名（前缀组合）
                        const prefixDomain = `${combination}${keyword}.${tld}`;
                        generatedDomains.push(prefixDomain);
                    }
                }
            });
        });
        
        // 去重
        generatedDomains = [...new Set(generatedDomains)];
        
        // 显示生成的域名
        displayGeneratedDomains();
        
        // 启用查询按钮
        queryButton.disabled = false;
    }
    
    // 生成组合
    function generateCombinations(type, length) {
        let chars = [];
        const combinations = [''];
        
        // 根据类型添加字符
        if (type === 'number' || type === 'both') {
            for (let i = 0; i <= 9; i++) {
                chars.push(i.toString());
            }
        }
        
        if (type === 'letter' || type === 'both') {
            for (let i = 97; i <= 122; i++) {
                chars.push(String.fromCharCode(i));
            }
        }
        
        // 如果不需要组合，直接返回空字符串
        if (type === 'none' || length === 0) {
            return combinations;
        }
        
        // 生成指定长度的所有组合
        for (let i = 1; i <= length; i++) {
            const tempCombinations = [];
            
            for (let j = 0; j < combinations.length; j++) {
                for (let k = 0; k < chars.length; k++) {
                    if (combinations[j].length === i - 1) {
                        tempCombinations.push(combinations[j] + chars[k]);
                    }
                }
            }
            
            combinations.push(...tempCombinations);
        }
        
        return combinations;
    }
    
    // 显示生成的域名
    function displayGeneratedDomains() {
        if (generatedDomains.length === 0) {
            combinationsList.innerHTML = '<p>未生成任何域名组合</p>';
            return;
        }
        
        combinationsList.innerHTML = generatedDomains.map(domain => 
            `<div class="domain-item">${domain}</div>`
        ).join('');
        
        // 更新统计信息
        const combinationsDiv = document.getElementById('combinations');
        const h3 = combinationsDiv.querySelector('h3');
        h3.textContent = `生成的域名组合 (${generatedDomains.length}个)`;
    }
    
    // 批量查询域名
    async function batchQueryDomains() {
        if (generatedDomains.length === 0) {
            showError('请先生成域名组合');
            return;
        }
        
        // 清空之前的结果
        queryResults = {};
        resultsContent.innerHTML = '';
        availableList.innerHTML = '';
        
        // 显示加载状态
        showLoading('开始批量查询域名...');
        
        try {
            // 分批查询，避免请求过多
            const batchSize = 10;
            const availableDomains = [];
            const errorDomains = [];
            let totalProcessed = 0;
            
            for (let i = 0; i < generatedDomains.length; i += batchSize) {
                const batch = generatedDomains.slice(i, i + batchSize);
                
                // 更新加载状态
                const progress = Math.floor((i / generatedDomains.length) * 100);
                showLoading(`查询中: ${progress}% (${i}/${generatedDomains.length})`);
                
                try {
                    const batchResults = await queryDomainBatch(batch);
                    
                    // 更新结果
                    Object.assign(queryResults, batchResults);
                    
                    // 收集可注册的域名和错误域名
                    for (const domain in batchResults) {
                        totalProcessed++;
                        const result = batchResults[domain];
                        
                        if (result.error) {
                            errorDomains.push({ domain, error: result.error });
                        } else if (result.available) {
                            availableDomains.push(domain);
                        }
                    }
                    
                    // 实时更新UI
                    displayResults();
                    displayAvailableDomains(availableDomains, errorDomains);
                    
                } catch (batchError) {
                    console.error(`批量查询错误 (批次 ${Math.floor(i/batchSize) + 1}):`, batchError);
                    // 记录此批次的所有域名都出错
                    batch.forEach(domain => {
                        totalProcessed++;
                        errorDomains.push({ domain, error: '查询请求失败' });
                        queryResults[domain] = { available: false, error: '查询请求失败' };
                    });
                    displayResults();
                }
                
                // 添加延迟，避免请求过于频繁
                if (i + batchSize < generatedDomains.length) {
                    await new Promise(resolve => setTimeout(resolve, 800));
                }
            }
            
            // 显示最终统计信息
            showLoading(`查询完成: 共 ${generatedDomains.length} 个域名，${availableDomains.length} 个可注册`);
            
            // 短暂显示完成状态
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 切换到结果选项卡
            switchToTab('results');
            
        } catch (error) {
            console.error('批量查询过程中发生错误:', error);
            showError(`查询失败: ${error.message || '未知错误'}`);
        } finally {
            hideLoading();
        }
    }
    
    // 批量查询API
    async function queryDomainBatch(domains) {
        const response = await fetch('/api/whois-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domains: domains })
        });
        
        if (!response.ok) {
            throw new Error('网络响应错误');
        }
        
        return await response.json();
    }
    
    // 显示所有查询结果
    function displayResults() {
        const domainCount = Object.keys(queryResults).length;
        
        if (domainCount === 0) {
            resultsContent.innerHTML = '<p class="no-results">暂无查询结果</p>';
            return;
        }
        
        // 排序：先显示可注册的，再显示已注册的
        const domains = Object.keys(queryResults).sort((a, b) => {
            const statusA = queryResults[a].available ? 0 : 1;
            const statusB = queryResults[b].available ? 0 : 1;
            if (statusA !== statusB) return statusA - statusB;
            // 同状态下按长度排序
            return a.length - b.length;
        });
        
        const resultsHTML = domains.map(domain => {
            const result = queryResults[domain];
            let statusHTML, icon;
            
            if (result.error) {
                statusHTML = `<span class="status error">${result.error}</span>`;
                icon = '❌';
            } else if (result.available) {
                statusHTML = '<span class="status available">可注册</span>';
                icon = '✅';
                // 添加复制按钮给可注册域名
                return `
                    <div class="result-item">
                        <div class="result-content">
                            <span class="status-icon">${icon}</span>
                            <div class="domain">${domain}</div>
                            <div class="status">${statusHTML}</div>
                        </div>
                        <button class="copy-btn" onclick="copyToClipboard('${domain}')">复制</button>
                    </div>
                `;
            } else {
                statusHTML = '<span class="status registered">已注册</span>';
                icon = '❌';
            }
            
            return `
                <div class="result-item">
                    <div class="result-content">
                        <span class="status-icon">${icon}</span>
                        <div class="domain">${domain}</div>
                        <div class="status">${statusHTML}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        resultsContent.innerHTML = `
            <div class="results-header">
                <h3>查询结果 (${domainCount})</h3>
            </div>
            <div class="results-list">
                ${resultsHTML}
            </div>
        `;
    }
    
    // 显示可注册的域名和错误域名
    function displayAvailableDomains(availableDomains, errorDomains = []) {
        // 显示可注册域名
        if (availableDomains.length === 0) {
            availableList.innerHTML = '<p class="no-results">没有找到可注册的域名</p>';
        } else {
            // 按长度排序
            availableDomains.sort((a, b) => a.length - b.length);
            
            const listHTML = availableDomains.map(domain => `
                <div class="domain-item">
                    <span class="domain-name">${domain}</span>
                    <span class="status available">可注册</span>
                    <button class="copy-btn" onclick="copyToClipboard('${domain}')">复制</button>
                </div>
            `).join('');
            
            availableList.innerHTML = `
                <div class="results-header">
                    <h3>可注册域名 (${availableDomains.length})</h3>
                    <button class="copy-all-btn" onclick="copyToClipboard('${availableDomains.join('\n')}')">复制全部</button>
                </div>
                <div class="domains-container">
                    ${listHTML}
                </div>
            `;
        }
        
        // 显示错误域名
        if (errorDomains.length > 0) {
            const errorHTML = errorDomains.map(item => `
                <div class="domain-item error">
                    <span class="domain-name">${item.domain}</span>
                    <span class="status error">${item.error}</span>
                </div>
            `).join('');
            
            // 创建错误列表容器
            let errorContainer = document.getElementById('errorDomains');
            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.id = 'errorDomains';
                errorContainer.className = 'tab-content';
                document.querySelector('.tab-contents').appendChild(errorContainer);
                
                // 添加错误标签
                const errorTab = document.createElement('button');
                errorTab.className = 'tab-button';
                errorTab.textContent = `错误域名 (${errorDomains.length})`;
                errorTab.onclick = () => switchToTab('errorDomains');
                document.querySelector('.tab-buttons').appendChild(errorTab);
            }
            
            errorContainer.innerHTML = `
                <div class="results-header">
                    <h3>查询出错的域名 (${errorDomains.length})</h3>
                </div>
                <div class="domains-container error-list">
                    ${errorHTML}
                </div>
            `;
        }
        
        // 更新统计信息
        const availableDiv = document.getElementById('availableDomains');
        const h3 = availableDiv.querySelector('h3');
        h3.textContent = `可注册的域名 (${availableDomains.length}个)`;
    }
    
    // 创建错误提示模态框
    function createErrorModal() {
        if (!errorModal) {
            errorModal = document.createElement('div');
            errorModal.className = 'error-modal';
            errorModal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            `;
            
            const modalContent = document.createElement('div');
            modalContent.style.cssText = `
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                width: 90%;
            `;
            
            // 创建错误消息元素
            const errorMessage = document.createElement('p');
            errorMessage.style.cssText = `
                margin: 0 0 15px 0;
                color: #dc3545;
                font-size: 16px;
            `;
            
            const closeButton = document.createElement('button');
            closeButton.textContent = '关闭';
            closeButton.style.cssText = `
                margin-top: 15px;
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            `;
            closeButton.addEventListener('click', () => {
                errorModal.style.display = 'none';
            });
            
            modalContent.appendChild(errorMessage);
            modalContent.appendChild(closeButton);
            errorModal.appendChild(modalContent);
            document.body.appendChild(errorModal);
        }
        
        // 返回错误消息元素
        return errorModal.querySelector('p');
    }
    
    // 显示错误信息
    function showError(message) {
        const errorMessage = createErrorModal();
        errorMessage.textContent = message;
        errorModal.style.display = 'flex';
    }
    
    // 切换到指定选项卡
    function switchToTab(tabId) {
        const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
        if (tab) {
            tab.click();
        }
    }
    
    // 显示加载状态
    function showLoading(message = '处理中...') {
        if (loadingIndicator.querySelector('.loading-text')) {
            loadingIndicator.querySelector('.loading-text').textContent = message;
        } else {
            const loadingText = document.createElement('div');
            loadingText.className = 'loading-text';
            loadingText.textContent = message;
            loadingText.style.cssText = `
                margin-top: 10px;
                font-size: 14px;
                color: #666;
            `;
            loadingIndicator.appendChild(loadingText);
        }
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.flexDirection = 'column';
        loadingIndicator.style.alignItems = 'center';
        generateButton.disabled = true;
        queryButton.disabled = true;
    }
    
    // 隐藏加载状态
    function hideLoading() {
        loadingIndicator.style.display = 'none';
        generateButton.disabled = false;
        queryButton.disabled = false;
    }
    
    // 复制文本到剪贴板
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text)
            .then(() => {
                // 添加临时提示
                const notification = document.createElement('div');
                notification.className = 'copy-notification';
                notification.textContent = '已复制到剪贴板';
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.remove();
                }, 2000);
            })
            .catch(err => {
                console.error('复制失败:', err);
                showError('复制失败，请手动选择复制');
            });
    }
    
    // 将复制函数添加到window对象，使其在onclick属性中可用
    window.copyToClipboard = copyToClipboard;
    
    // 检查后端服务是否正常运行
    async function checkBackendHealth() {
        try {
            const response = await fetch('/health');
            if (!response.ok) {
                throw new Error('后端服务不可用');
            }
            return true;
        } catch (error) {
            console.warn('后端健康检查失败:', error);
            return false;
        }
    }
    
    // 初始化时检查后端健康状态
    checkBackendHealth().then(healthy => {
        if (!healthy) {
            showError('无法连接到后端服务，请确保服务正常运行');
        }
    });
});