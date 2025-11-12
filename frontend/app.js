document.addEventListener('DOMContentLoaded', function() {
    const domainInput = document.getElementById('domainInput');
    const queryButton = document.getElementById('queryButton');
    const resultDiv = document.getElementById('result');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const historyContainer = document.getElementById('historyContainer');
    
    // 加载查询历史
    loadHistory();
    
    // 查询按钮点击事件
    queryButton.addEventListener('click', function() {
        queryDomain();
    });
    
    // 回车键查询
    domainInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            queryDomain();
        }
    });
    
    // 历史记录点击事件委托
    historyContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('history-item')) {
            domainInput.value = event.target.textContent.trim();
            queryDomain();
        }
    });
    
    function queryDomain() {
        const domain = domainInput.value.trim();
        
        if (!domain) {
            showError('请输入域名');
            return;
        }
        
        if (!isValidDomain(domain)) {
            showError('请输入有效的域名格式');
            return;
        }
        
        showLoading();
        
        // 调用后端API - 使用相对路径以便部署在服务器上时调用内部API
        fetch('/api/whois', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: domain })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showError(data.error);
            } else {
                showResult(data.whois_data);
                addToHistory(domain);
            }
        })
        .catch(error => {
            hideLoading();
            showError('查询失败: ' + error.message);
        });
    }
    
    function isValidDomain(domain) {
        // 简单的域名格式验证
        const domainRegex = /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
        return domainRegex.test(domain);
    }
    
    function showLoading() {
        loadingIndicator.style.display = 'block';
        resultDiv.textContent = '';
        resultDiv.className = '';
    }
    
    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }
    
    function showResult(data) {
        resultDiv.textContent = data;
        resultDiv.className = '';
    }
    
    function showError(message) {
        resultDiv.textContent = message;
        resultDiv.className = 'error';
    }
    
    function addToHistory(domain) {
        // 获取现有历史
        let history = JSON.parse(localStorage.getItem('whoisHistory') || '[]');
        
        // 移除重复项
        history = history.filter(item => item !== domain);
        
        // 添加到开头
        history.unshift(domain);
        
        // 限制历史记录数量
        if (history.length > 10) {
            history = history.slice(0, 10);
        }
        
        // 保存到localStorage
        localStorage.setItem('whoisHistory', JSON.stringify(history));
        
        // 更新UI
        renderHistory(history);
    }
    
    function loadHistory() {
        const history = JSON.parse(localStorage.getItem('whoisHistory') || '[]');
        renderHistory(history);
    }
    
    function renderHistory(history) {
        if (history.length === 0) {
            historyContainer.innerHTML = '<p>暂无查询历史</p>';
            return;
        }
        
        const historyHTML = history.map(domain => 
            `<div class="history-item">${domain}</div>`
        ).join('');
        
        historyContainer.innerHTML = historyHTML;
    }
});