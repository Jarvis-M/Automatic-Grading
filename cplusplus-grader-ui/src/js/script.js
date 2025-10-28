// =====================  part 1:全局配置   =======================
const CONFIG = {
    API_BASE_URL: 'http://localhost:5000', // 后端API地址(Flask默认端口)
    POLLING_INTERVAL: 2000, // 轮询间隔2秒
    MAX_POLLING_ATTEMPTS: 30 // 最多轮询30次
};


// ===================  part 2: 工具函数  ==============================
// 工具函数：显示消息
//function showMessage(message, type = 'info') {
//    // 在实际项目中可以替换为更美观的Toast组件
//    alert(`${type.toUpperCase()}: ${message}`);
//}

// 工具函数：显示警告弹窗
function showAlert(message) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'alert-overlay';
    
    // 创建弹窗
    const modal = document.createElement('div');
    modal.className = 'alert-modal';
    modal.innerHTML = `
        <p>${message}</p>
        <button class="btn btn-primary" id="alertConfirmBtn">确认</button>
    `;
    
    // 添加到页面
    document.body.appendChild(overlay);
    document.body.appendChild(modal);
    
    // 确认按钮事件
    document.getElementById('alertConfirmBtn').addEventListener('click', () => {
        document.body.removeChild(overlay);
        document.body.removeChild(modal);
    });
    
    // 点击遮罩层也可以关闭
    overlay.addEventListener('click', () => {
        document.body.removeChild(overlay);
        document.body.removeChild(modal);
    });
}

// 工具函数：显示/隐藏元素
function toggleElement(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = show ? 'block' : 'none';
    }
}

//======================  part3: API函数（全局可访问）  =====================
async function realUploadToBackend(file) {
        const formData = new FormData();
        formData.append('file',file)
        //后端支持添加学号的话
        //formData.append('student_id', studentId)

        try{
            const response = await fetch(`${CONFIG.API_BASE_URL}/upload`,{
                method: 'POST',
                body: formData,
            });

            if (!response.ok){
                throw new Error(`上传失败:${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            //根据后端返回格式处理
            if(result.message && result.message.includes('successfully')){
                return result.filepath;//返回文件路径，用于后续AI评分
            }else{
                throw new Error(result.error || '上传处理失败');
            }
           
        } catch(error){
            console.error('上传API错误:', error);
            throw error;
        }
    }

// 获取结果
async function realFetchResult(filepath) {
    //真实的获取AI评分
    try{
        const response = await fetch(`${CONFIG.API_BASE_URL}/ai_score`,{
            method: 'POST',
            headers:{
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filepath: filepath
            })
        });

        if(!response.ok){
            throw new Error(`获取评分失败: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        //根据后端返回格式处理
        if(result.score_breakdown){
            return result;
                /**
                 * {
                 * student_id: studentId,
                 * total_score: result.score_breakdown.total,
                 * ai_feedback: formatAIFeedback(result)//格式化后端返回的数据
                 * };
                 */
                
            
        } else {
            throw new Error(result.error || '评分数据缺失');
        }
    } catch (error){
        console.error('获取评分API错误', error);
        throw error;
    }
}

//格式化AI反馈为HTML
function formatAIFeedback(apiResult){
    const breakdown = apiResult.score_breakdown;
    const rationale = apiResult.rationale;
    const suggestions = apiResult.suggestions;

    let feedbackHTML = `
    <h3>📊 评分细则</h3>
        <ul>
            <li><strong>可编译性：</strong>${breakdown.compilability}分</li>
            <li><strong>正确性：</strong>${breakdown.correctness}分</li>
            <li><strong>代码质量：</strong>${breakdown.code_quality}分</li>
            <li><strong>可读性：</strong>${breakdown.readability}分</li>
            <li><strong>总分：</strong>${breakdown.total}分</li>
        </ul>

        <h3>📝 评分理由</h3>
    <p>${rationale}</p>
    `;

    if (suggestions && suggestions.length > 0){
        feedbackHTML += `
            <h3>💡 改进建议</h3>
            <ul>
        `;
        suggestions.forEach(suggestion => {
            feedbackHTML += `<li>${suggestion}</li>`;
        });
        feedbackHTML += `</ul>`;    
    }

    return feedbackHTML;
}


//=======================  part4:页面功能  =============================

// 上传页面功能初始化
function initUploadPage() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const confirmBtn = document.getElementById('confirmBtn');
    const reuploadBtn = document.getElementById('reuploadBtn');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const previewFilename = document.getElementById('previewFilename');
    const uploadStatus = document.getElementById('uploadStatus');
    const studentIdInput = document.getElementById('studentId');
    //const navLinks = document.querySelectorAll('.nav-link');
    
    let selectedFile = null;

    // 为导航链接添加点击事件（防止未上传时跳转）
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === 'result.html'){
            link.addEventListener('click', (e) => {
                if(!selectedFile){
                    e.preventDefault();
                    showAlert('请先上传图片并获取评分');
                }
            });
        }
    });

    /**
     * navLinks.forEach(link => {
     *   if (link.getAttribute('href') === 'result.html') {
     *       link.addEventListener('click', (e) => {
     *           if (!selectedFile) {
     *               e.preventDefault();
     *               showAlert('请先上传图片');
     *          }
     *       });
     *   }
     * }); 
     */
    

    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 拖拽功能
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // 文件选择变化
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // 处理选中的文件
    function handleFileSelect(file) {
        if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
            selectedFile = file;
            
            // 显示预览
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImage.src = e.target.result;
                previewFilename.textContent = `文件: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                
                // 显示预览区域，隐藏上传提示
                toggleElement('uploadArea', false);
                toggleElement('previewArea', true);
            };
            reader.readAsDataURL(file);
            
            confirmBtn.disabled = false;
        } else {
            //showMessage('请选择JPG或PNG格式的图片文件！');
            showAlert('请选择JPG或PNG格式的图片文件！');

        }
    }

    // 确认按钮点击 - 上传图片
    confirmBtn.addEventListener('click', async () => {
        if (!studentIdInput.value.trim()) {
            showAlert('请输入学号');
            return
        } 
        if(!selectedFile){
            //await uploadAndProcessImage(selectedFile,studentIdInput.value.trim());
            showAlert('请先选择要上传的图片！');
            return;
        }
        //}else{
        //   showAlert('请先选择要上传的图片！');
        //}
        await uploadAndProcessImage(selectedFile,studentIdInput.value.trim());
    });

    // 重新上传按钮
    reuploadBtn.addEventListener('click', () => {
        if(!selectedFile){
            showAlert('请先上传图片');
            return;
        }
        resetUploadState();
    });

    // 重置上传状态
    function resetUploadState() {
        fileInput.value = '';
        selectedFile = null;
        previewImage.src = '';
        
        toggleElement('uploadArea', true);
        toggleElement('previewArea', false);
        toggleElement('uploadStatus', false);
        
        confirmBtn.disabled = true;
        confirmBtn.textContent = '确认上传';
    }

    // 上传和处理图片
    async function uploadAndProcessImage(file,studentId) {
        try {
            // 显示上传状态
            toggleElement('uploadStatus', true);
            confirmBtn.disabled = true;
            confirmBtn.textContent = '处理中...';
            
            
            // ========== 模拟2数据测试 ==========
            
            // 模拟处理延迟
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // 创建模拟结果数据
            const result = {
                student_id: studentId, // 使用前端输入的学号
                total_score: Math.floor(Math.random() * 30) + 70, // 70-100的随机分数
                ai_feedback: `
                    <h3>📊 评分细则（模拟数据）</h3>
                    <ul>
                        <li><strong>可编译性：</strong>20/20分 - 代码一次性编译通过</li>
                        <li><strong>正确性：</strong>35/40分 - 通过7/8个测试用例</li>
                        <li><strong>代码质量：</strong>18/20分 - 结构清晰，命名规范</li>
                        <li><strong>鲁棒性：</strong>8/10分 - 有基础异常处理</li>
                        <li><strong>文档与可读性：</strong>4/10分 - 缺少必要注释</li>
                    </ul>
                    
                    <h3>📝 评分理由</h3>
                    <p>代码逻辑清晰，基本功能实现完整，但在边界条件处理上可以更加完善。</p>
                    
                    <h3>💡 改进建议</h3>
                    <ul>
                        <li>建议在关键函数前添加注释，说明其功能和参数</li>
                        <li>第25行的循环可以优化，避免不必要的计算</li>
                        <li>考虑使用更描述性的变量名，提高代码可读性</li>
                        <li>可以添加更多的输入验证来增强程序的健壮性</li>
                    </ul>
                `
            };
            
            console.log('模拟处理完成，准备跳转:', result);


            /*
            // 模拟1上传到后端
            const taskId = await mockUploadToBackend(file,studentId);
            
            // 跳转到结果页面，传递taskId和studentId
            window.location.href = `result.html?task_id=${taskId}&student_id=${studentId}`;
            */

            /*
            //==============  真实API调用  ====================
            //1.先上传文件
            //const filepath = await realUploadToBackend(file, studentId);
            const filepath = await realUploadToBackend(file);

            //2.然后获取AI评分
            //const result = await realFetchResult(filepath,studentId);
            const apiResult = await realFetchResult(filepath);

            //3.准备结果数据
            const result = {
                student_id: studentId, // 使用前端输入的学号
                total_score: apiResult.score_breakdown.total,
                ai_feedback: formatAIFeedback(apiResult)
            };
            */
            //3.跳转到结果页面，传递数据
            //由于数据较多，尝试使用URL参数传递基本信息，或者使用sessionStorage
            sessionStorage.setItem('gradingResult', JSON.stringify(result));
            //window.location.href = `result.html?student_id=${studentId}`;
            window.location.href = `result.html`;
            
        } catch (error) {
            console.error('上传错误:', error);
            showAlert('处理失败：' + error.message);
            resetUploadState();
        }
    }

    // 后端上传

    /**将学生id手动输入后传递到后端
        async function realUploadToBackend(file,studentId) {
        const formData = new FormData();
        formData.append('file',file)
        //后端支持添加学号的话
        //formData.append('student_id', studentId)

        try{
            const response = await fetch(`${CONFIG.API_BASE_URL}/upload`,{
                method: 'POST',
                body: formData,
            });

            if (!response.ok){
                throw new Error(`上传失败:${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            //根据后端返回格式处理
            if(result.message && result.message.includes('successfully')){
                return result.filepath;//返回文件路径，用于后续AI评分
            }else{
                throw new Error(result.error || '上传处理失败');
            }
           
        } catch(error){
            console.error('上传API错误:', error);
            throw error;
        }
        /**模拟后端上传
         * return new Promise((resolve) => {
            setTimeout(() => {
                // 生成taskId
                const taskId = 'mock_task_' + Date.now();
                console.log(`模拟上传成功，文件名: ${file.name}, 学号: ${studentId}, taskId: ${taskId}`);
                resolve(taskId);
            }, 2000);
            });
            }
        **/
    
    // 初始状态禁用确认按钮
    confirmBtn.disabled = true;
}

// 结果页面功能初始化
function initResultPage() {
    const uploadAgainBtn = document.getElementById('uploadAgainBtn');
    const aiContent = document.getElementById('aiContent');
    const loadingContent = document.getElementById('loadingContent');
    const studentScore = document.getElementById('studentScore');

    /**
     * // 从URL获取
        const urlParams = new URLSearchParams(window.location.search);
        const taskId = urlParams.get('task_id') || 'demo_001';
        const studentId = urlParams.get(student_id) || '001';

        //立即更新学号显示（从URL参数获取）
        studentScore.textContent = `${studentId} - 加载中...`;

        // 获取评分结果
        fetchResult(taskId,studentId);

        // 获取结果
    async function fetchResult(taskId, studentId) {
        try {
            // 模拟从后端获取结果
            const result = await mockFetchResult(taskId, studentId);
            displayResult(result);
            
        } catch (error) {
            console.error('获取结果错误:', error);
            showAlert('获取评分结果失败');
            displayError();
        }
    }

     */
    
    //从sessionStorage获取结果
    const resultJson = sessionStorage.getItem('gradingResult');

    /*
    if(resultJson){
        const result = JSON.parse(resultJson);
        displayResult(result);
        //清除存储的数据
        sessionStorage.removeItem('gradingResult');
    }else{
        //如果没有数据，显示错误
        displayError('没有找到评分结果，请重新上传');
    }
    */
   if (resultJson) {
        try {
            const result = JSON.parse(resultJson);
            console.log('从sessionStorage获取结果:', result);
            displayResult(result);
            sessionStorage.removeItem('gradingResult');
        } catch (error) {
            console.error('解析结果失败:', error);
            displayError('数据解析失败，请重新上传');
        }
    } else {
        displayError('没有找到评分结果，请先上传图片并获取评分');
    }

    //再次上传按钮
    uploadAgainBtn.addEventListener('click', () =>{
        window.location.href = 'index.html';
    });


    // 显示结果
    function displayResult(result) {
        // 隐藏加载状态
        loadingContent.style.display = 'none';
        
        // 更新学号和分数
        //studentScore.textContent = `${result.student_id} - ${result.total_score}分`;
        studentScore.textContent = `${result.student_id} - ${result.total_score}分`;
        
        // 显示AI内容
        aiContent.innerHTML = result.ai_feedback;
    }

    // 显示错误状态
    function displayError(message) {
        // 更新标题显示错误状态
        studentScore.textContent = '加载失败';
        studentScore.style.color = '#e74c3c';

        loadingContent.innerHTML = `
            <div style="color: #e74c3c; text-align: center;">
                <p>❌ ${message}</p>
                <button class="btn btn-primary" onclick="window.location.href='index.html'" style="margin-top: 1rem;">返回上传页面</button>
            </div>
        `;
    }

    
        /** 
        return new Promise((resolve) => {
            setTimeout(() => {
                const result = {
                    student_id: studentId,
                    total_score: Math.floor(Math.random() * 30) + 70, // 70-100的随机分
                    ai_feedback: generateMockFeedback()
                };
                console.log(`模拟获取结果成功，taskId: ${taskId}, 学号: ${studentId}`);
                resolve(result);
            }, 3000);
        });
        */
}

    


    /** 
    // 生成模拟的AI反馈
    function generateMockFeedback() {
        return `
            <h3>📊 评分细则</h3>
            <ul>
                <li><strong>可编译性：</strong>20/20分 - 代码一次性编译通过</li>
                <li><strong>正确性：</strong>35/40分 - 通过7/8个测试用例</li>
                <li><strong>代码质量：</strong>18/20分 - 结构清晰，命名规范</li>
                <li><strong>鲁棒性：</strong>8/10分 - 有基础异常处理</li>
                <li><strong>文档与可读性：</strong>4/10分 - 缺少必要注释</li>
            </ul>
            
            <h3>💡 改进建议</h3>
            <p>1. 代码逻辑清晰，但在边界条件处理上可以更加完善。</p>
            <p>2. 建议在关键函数前添加注释，说明其功能和参数。</p>
            <p>3. 第25行的循环可以优化，避免不必要的计算。</p>
            <p>4. 考虑使用更描述性的变量名，提高代码可读性。</p>
            <p>5. 可以添加更多的输入验证来增强程序的健壮性。</p>
        `;
    }
    */



//=======================  part4:页面初始化  ==========================
// 页面初始化
document.addEventListener('DOMContentLoaded', function(){
    // 根据当前页面初始化相应的功能
    if (document.querySelector('.upload-card')) {
        initUploadPage();
    }
    
    if (document.querySelector('.result-card')) {
        initResultPage();
    }
});