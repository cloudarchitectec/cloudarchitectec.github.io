// Enhanced Chinese search functionality for PaperMod
// This extends the existing fastsearch.js with Chinese-specific features

// Chinese character detection
function containsChinese(text) {
    return /[\u4e00-\u9fff\u3400-\u4dbf]/.test(text);
}

// Simple Traditional to Simplified Chinese conversion (common characters)
const traditionalToSimplified = {
    '繁': '繁', '體': '体', '中': '中', '文': '文',
    '雲': '云', '端': '端', '架': '架', '構': '构',
    '師': '师', '專': '专', '業': '业', '技': '技',
    '術': '术', '部': '部', '落': '落', '格': '格',
    '澳': '澳', '洲': '洲', '生': '生', '活': '活',
    '職': '职', '場': '场', '文': '文', '化': '化',
    '旅': '旅', '行': '行', '觀': '观', '察': '察',
    '筆': '笔', '記': '记', '經': '经', '驗': '验',
    '分': '分', '享': '享', '學': '学', '習': '习',
    '工': '工', '作': '作', '轉': '转', '換': '换',
    '職': '职', '涯': '涯', '諮': '咨', '詢': '询',
    '服': '服', '務': '务', '臺': '台', '灣': '湾',
    '女': '女', '打': '打', '度': '度', '假': '假',
    '移': '移', '民': '民', '組': '组', '程': '程',
    '師': '师', '入': '入', '微': '微', '軟': '软',
    '國': '国', '家': '家', '致': '致', '力': '力',
    '於': '于', '式': '式', '體': '体', '驗': '验',
    '希': '希', '望': '望', '跟': '跟', '大': '大',
    '資': '资', '料': '料', '科': '科', '管': '管',
    '理': '理', '開': '开', '發': '发', '設': '设',
    '計': '计', '網': '网', '路': '路', '安': '安',
    '全': '全', '數': '数', '據': '据', '庫': '库',
    '系': '系', '統': '统', '應': '应', '用': '用',
    '軟': '软', '體': '体', '硬': '硬', '體': '体',
    '網': '网', '絡': '络', '伺': '伺', '服': '服',
    '器': '器', '資': '资', '訊': '讯', '處': '处',
    '理': '理', '儲': '储', '存': '存', '備': '备',
    '份': '份', '恢': '恢', '復': '复', '監': '监',
    '控': '控', '維': '维', '護': '护', '優': '优',
    '化': '化', '測': '测', '試': '试', '除': '除',
    '錯': '错', '佈': '布', '署': '署', '運': '运',
    '營': '营', '維': '维', '運': '运', '協': '协',
    '作': '作', '團': '团', '隊': '队', '專': '专',
    '案': '案', '計': '计', '畫': '画', '執': '执',
    '行': '行', '管': '管', '理': '理', '品': '品',
    '質': '质', '保': '保', '證': '证', '流': '流',
    '程': '程', '標': '标', '準': '准', '規': '规',
    '範': '范', '文': '文', '件': '件', '報': '报',
    '告': '告', '簡': '简', '報': '报', '會': '会',
    '議': '议', '訓': '训', '練': '练', '教': '教',
    '育': '育', '學': '学', '習': '习', '認': '认',
    '證': '证', '考': '考', '試': '试', '證': '证',
    '照': '照', '執': '执', '業': '业', '資': '资',
    '格': '格', '技': '技', '能': '能', '競': '竞',
    '賽': '赛', '獎': '奖', '項': '项', '成': '成',
    '就': '就', '榮': '荣', '譽': '誉', '表': '表',
    '揚': '扬', '升': '升', '遷': '迁', '調': '调',
    '職': '职', '轉': '转', '換': '换', '跑': '跑',
    '道': '道', '機': '机', '會': '会', '挑': '挑',
    '戰': '战', '困': '困', '難': '难', '問': '问',
    '題': '题', '解': '解', '決': '决', '方': '方',
    '案': '案', '策': '策', '略': '略', '規': '规',
    '劃': '划', '目': '目', '標': '标', '達': '达',
    '成': '成', '績': '绩', '效': '效', '評': '评',
    '估': '估', '考': '考', '核': '核', '獎': '奖',
    '勵': '励', '懲': '惩', '罰': '罚', '福': '福',
    '利': '利', '待': '待', '遇': '遇', '薪': '薪',
    '資': '资', '獎': '奖', '金': '金', '紅': '红',
    '利': '利', '假': '假', '期': '期', '保': '保',
    '險': '险', '退': '退', '休': '休', '金': '金',
    '健': '健', '康': '康', '檢': '检', '查': '查',
    '醫': '医', '療': '疗', '補': '补', '助': '助'
};

function convertToSimplified(text) {
    return text.split('').map(char => traditionalToSimplified[char] || char).join('');
}

// Basic pinyin conversion (limited set for common tech terms)
const pinyinMap = {
    '雲端': 'yunduan', '架構': 'jiagou', '工程師': 'gongchengshi',
    '軟體': 'ruanti', '開發': 'kaifa', '程式': 'chengshi',
    '資料': 'ziliao', '數據': 'shuju', '系統': 'xitong',
    '網路': 'wanglu', '安全': 'anquan', '測試': 'ceshi',
    '部署': 'bushu', '維護': 'weihu', '優化': 'youhua',
    '監控': 'jiankong', '備份': 'beifen', '恢復': 'huifu',
    '澳洲': 'aozhou', '臺灣': 'taiwan', '生活': 'shenghuo',
    '工作': 'gongzuo', '職場': 'zhichang', '經驗': 'jingyan',
    '學習': 'xuexi', '成長': 'chengzhang', '挑戰': 'tiaozhan',
    '機會': 'jihui', '技術': 'jishu', '專業': 'zhuanye',
    '能力': 'nengli', '技能': 'jineng', '知識': 'zhishi',
    '經歷': 'jingli', '背景': 'beijing', '教育': 'jiaoyu',
    '訓練': 'xunlian', '認證': 'renzheng', '證照': 'zhenzhao',
    '考試': 'kaoshi', '面試': 'mianshi', '履歷': 'luli',
    '求職': 'qiuzhi', '轉職': 'zhuanzhi', '升遷': 'shengqian',
    '薪資': 'xinzi', '待遇': 'daiyu', '福利': 'fuli',
    '假期': 'jiaqi', '保險': 'baoxian', '退休': 'tuixiu'
};

function addPinyinToText(text) {
    let result = text;
    for (const [chinese, pinyin] of Object.entries(pinyinMap)) {
        if (text.includes(chinese)) {
            result += ' ' + pinyin;
        }
    }
    return result;
}

// Enhanced search function that works with the existing PaperMod search
function enhanceChineseSearch() {
    // Wait for the original search to be initialized
    const checkForOriginalSearch = setInterval(() => {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        if (searchInput && searchResults && window.fuse) {
            clearInterval(checkForOriginalSearch);
            initializeEnhancedSearch();
        }
    }, 100);
}

function initializeEnhancedSearch() {
    const searchInput = document.getElementById('searchInput');
    const originalData = window.fuse._docs || [];
    
    // Enhance the search data with additional searchable content
    const enhancedData = originalData.map(item => ({
        ...item,
        enhancedContent: [
            item.title || '',
            item.content || '',
            item.summary || '',
            convertToSimplified(item.title || ''),
            convertToSimplified(item.content || ''),
            convertToSimplified(item.summary || ''),
            addPinyinToText(item.title || ''),
            addPinyinToText(item.content || ''),
            addPinyinToText(item.summary || '')
        ].join(' ')
    }));
    
    // Update Fuse configuration for enhanced Chinese search
    const enhancedOptions = {
        includeScore: true,
        includeMatches: true,
        threshold: 0.2,
        location: 0,
        distance: 50,
        maxPatternLength: 32,
        minMatchCharLength: 1,
        ignoreLocation: true,
        keys: [
            { name: 'title', weight: 0.4 },
            { name: 'content', weight: 0.3 },
            { name: 'summary', weight: 0.2 },
            { name: 'enhancedContent', weight: 0.1 }
        ]
    };
    
    // Create new Fuse instance with enhanced data
    window.enhancedFuse = new Fuse(enhancedData, enhancedOptions);
    
    // Override the original search behavior
    let searchTimeout;
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performEnhancedSearch(e.target.value.trim());
        }, 300);
    });
    
    // Add search suggestions
    addSearchSuggestions();
}

function performEnhancedSearch(query) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!query || query.length === 0) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    // Search with multiple query variations
    const queries = [
        query,
        convertToSimplified(query),
        // Add common English tech terms if searching in Chinese
        containsChinese(query) ? '' : query
    ].filter(q => q);
    
    let allResults = [];
    
    queries.forEach(q => {
        if (window.enhancedFuse) {
            const results = window.enhancedFuse.search(q);
            allResults = allResults.concat(results);
        }
    });
    
    // Remove duplicates and sort by score
    const uniqueResults = allResults.filter((result, index, self) => 
        index === self.findIndex(r => r.item.permalink === result.item.permalink)
    ).sort((a, b) => a.score - b.score);
    
    // Display results (reuse PaperMod's display logic but enhance it)
    displayEnhancedResults(uniqueResults, query);
}

function displayEnhancedResults(results, query) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `<li><p>找不到包含 "${query}" 的文章</p></li>`;
        return;
    }
    
    let html = '';
    results.slice(0, 10).forEach(result => {
        const item = result.item;
        const score = Math.round((1 - result.score) * 100);
        
        html += `
            <li>
                <a href="${item.permalink}" tabindex="0">
                    <div class="search-result-title">${highlightMatches(item.title, query)}</div>
                    <div class="search-result-summary">${highlightMatches(item.summary || '', query)}</div>
                    <div class="search-result-meta">相關度: ${score}%</div>
                </a>
            </li>
        `;
    });
    
    resultsContainer.innerHTML = html;
}

function highlightMatches(text, query) {
    if (!text || !query) return text;
    
    const regex = new RegExp(`(${query.split('').join('|')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function addSearchSuggestions() {
    const searchInput = document.getElementById('searchInput');
    
    // Common search terms in both Traditional and Simplified Chinese
    const suggestions = [
        '雲端架構', '軟體開發', 'AWS', 'Azure', '微軟',
        'Amazon', '程式設計', '資料科學', '機器學習',
        '人工智慧', '網路安全', '系統管理', '資料庫',
        '澳洲生活', '職場經驗', '技術分享', '學習心得',
        '面試準備', '履歷撰寫', '轉職心得', '工作機會'
    ];
    
    searchInput.setAttribute('list', 'search-suggestions');
    
    const datalist = document.createElement('datalist');
    datalist.id = 'search-suggestions';
    
    suggestions.forEach(suggestion => {
        const option = document.createElement('option');
        option.value = suggestion;
        datalist.appendChild(option);
    });
    
    searchInput.parentNode.appendChild(datalist);
}

// Add enhanced CSS styles
function addEnhancedStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .search-result-title {
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }
        
        .search-result-summary {
            color: var(--content);
            font-size: 0.9rem;
            line-height: 1.4;
            margin-bottom: 0.25rem;
        }
        
        .search-result-meta {
            font-size: 0.8rem;
            color: var(--secondary);
            opacity: 0.8;
        }
        
        #searchResults li a {
            display: block;
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            text-decoration: none;
            transition: background-color 0.2s ease;
        }
        
        #searchResults li a:hover,
        #searchResults li a:focus {
            background-color: var(--code-bg);
        }
        
        mark {
            background-color: #fff3cd;
            color: #856404;
            padding: 0 2px;
            border-radius: 2px;
        }
        
        [data-theme="dark"] mark {
            background-color: #664d03;
            color: #fff3cd;
        }
        
        #searchInput {
            font-family: inherit;
        }
    `;
    
    document.head.appendChild(style);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only run on search page
    if (window.location.pathname.includes('/search')) {
        addEnhancedStyles();
        enhanceChineseSearch();
    }
});

// Also initialize if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.location.pathname.includes('/search')) {
            addEnhancedStyles();
            enhanceChineseSearch();
        }
    });
} else {
    if (window.location.pathname.includes('/search')) {
        addEnhancedStyles();
        enhanceChineseSearch();
    }
}