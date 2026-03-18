// ============================================================================
// OverFitting Search Engine — Frontend Logic
// ============================================================================

let currentMode = 'hybrid';

// ============================================================================
// Init
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    setMode('hybrid');
    loadStats();

    const input = document.getElementById('search-input');
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') performSearch();
    });
    input.addEventListener('input', () => {
        document.getElementById('clear-btn').style.display = input.value ? 'block' : 'none';
    });
    input.focus();
});

// ============================================================================
// Mode
// ============================================================================

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.mode === mode);
    });
}

// ============================================================================
// Quick Search / Clear
// ============================================================================

function quickSearch(query) {
    document.getElementById('search-input').value = query;
    document.getElementById('clear-btn').style.display = 'block';
    performSearch();
}

function clearSearch() {
    const input = document.getElementById('search-input');
    input.value = '';
    input.focus();
    document.getElementById('clear-btn').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('empty').style.display = 'none';
    document.getElementById('welcome').style.display = 'block';
}

// ============================================================================
// Search
// ============================================================================

async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    currentQuery = query;
    // UI state
    document.getElementById('welcome').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('empty').style.display = 'none';
    document.getElementById('loading').style.display = 'block';

    try {
        const params = new URLSearchParams({ q: query, mode: currentMode, top_k: 1000, alpha: 0.65 });
        const res = await fetch(`/api/search?${params}`);
        const data = await res.json();

        document.getElementById('loading').style.display = 'none';

        if (data.results && data.results.length > 0) {
            // Apply threshold filter (e.g. 25% minimum relevance)
            const rawResults = data.results;
            const tempMaxScore = rawResults[0].score > 0 ? rawResults[0].score : 1;
            const threshold = 15; // Ngưỡng 15%
            
            const validResults = rawResults.filter(r => {
                const pct = Math.round((r.score / tempMaxScore) * 100);
                return pct >= threshold;
            });

            if (validResults.length > 0) {
                data.results = validResults;
                data.total = validResults.length;
                renderResults(data);
            } else {
                document.getElementById('empty').style.display = 'block';
            }
        } else {
            document.getElementById('empty').style.display = 'block';
        }
    } catch (err) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('empty').style.display = 'block';
        console.error(err);
    }
}

let allResults = [];
let filteredResults = [];
let currentQuery = '';
let maxScore = 1;
let currentDisplayed = 0;
const PAGE_SIZE = 10;

// ============================================================================
// Province Dynamic Extraction
// ============================================================================
function extractProvince(address) {
    if (!address) return null;
    const parts = address.split(',');
    let last = parts[parts.length - 1].trim();
    last = last.replace(/^(tỉnh|thành phố|tp\.|tp)\s+/i, '').trim();
    if (last.toLowerCase() === 'hcm' || last.toLowerCase() === 'hồ chí minh' || last.toLowerCase() === 'tp hồ chí minh') return 'Hồ Chí Minh';
    if (last.toLowerCase() === 'hn') return 'Hà Nội';
    return last;
}

function updateProvinceDropdown(results) {
    const select = document.getElementById('province-filter');
    if (!select) return;
    
    const provinces = new Set();
    results.forEach(r => {
        const p = extractProvince(r.address);
        if (p) provinces.add(p);
    });
    
    const sortedProvinces = Array.from(provinces).sort((a, b) => a.localeCompare(b, 'vi'));
    let html = '<option value="all">Toàn quốc (Tất cả)</option>';
    sortedProvinces.forEach(p => {
        html += `<option value="${p}">${p}</option>`;
    });
    
    select.innerHTML = html;
}

// ============================================================================
// Render Results (Pagination)
// ============================================================================

function renderResults(data) {
    allResults = data.results;
    filteredResults = allResults;
    maxScore = allResults.length > 0 && allResults[0].score > 0 ? allResults[0].score : 1;
    currentDisplayed = 0;
    
    // Auto-populate custom province dropdown
    updateProvinceDropdown(allResults);
    
    // Reset filter states
    document.getElementById('status-filter').value = 'all';
    const pFilter = document.getElementById('province-filter');
    if (pFilter) pFilter.value = 'all';
    
    document.getElementById('results-list').innerHTML = '';
    
    // Mode labels
    const modeLabels = { bm25: 'Từ khoá', vector: 'Semantic', hybrid: 'Hybrid Search' };
    const modeLabel = modeLabels[data.mode] || data.mode;

    // Summary
    document.getElementById('results-summary').innerHTML =
        `Tìm thấy <strong>${data.total}</strong> kết quả (hiển thị trang). Phản hồi trong <strong>${data.time_ms}ms</strong> <span class="mode-badge">${modeLabel}</span>`;

    loadMore();
    document.getElementById('results-section').style.display = 'block';
}

function loadMore() {
    const list = document.getElementById('results-list');
    const container = document.getElementById('load-more-container');
    
    const end = Math.min(currentDisplayed + PAGE_SIZE, filteredResults.length);
    const sliceData = filteredResults.slice(currentDisplayed, end);
    
    sliceData.forEach((r, i) => {
        const rank = currentDisplayed + i + 1;

        // Relevance percentage (normalize top result = 100%)
        const pct = maxScore > 0 ? Math.round((r.score / maxScore) * 100) : 0;
        let relClass = 'relevance-high';
        if (pct < 60) relClass = 'relevance-low';
        else if (pct < 85) relClass = 'relevance-mid';

        // Rank badge
        let rankClass = '';
        if (rank === 1) rankClass = 'gold';
        else if (rank === 2) rankClass = 'silver';
        else if (rank === 3) rankClass = 'bronze';

        // Status
        const status = r.status || '';
        const isActive = !status.toLowerCase().includes('ngừng') && !status.toLowerCase().includes('giải thể');
        const statusClass = isActive ? 'status-active' : 'status-inactive';
        const statusDot = isActive ? '●' : '○';

        const card = document.createElement('div');
        card.className = 'result-card';
        card.style.animationDelay = `${i * 0.04}s`;

        card.innerHTML = `
            <div class="result-dense-body">
                <a href="javascript:void(0)" class="result-title" onclick="showDetail(${currentDisplayed + i})">${esc(r.company_name || 'Unnamed')}</a>
                <div class="result-url">MST: ${esc(r.tax_code || 'N/A')} &nbsp;·&nbsp; Đại diện: ${esc(r.representative || 'Chưa cập nhật')} <button class="copy-btn-inline" onclick="copyMST('${esc(r.tax_code)}')">Copy MST</button></div>
                <div class="result-snippet">${esc(r.address || 'N/A')}</div>
                ${r.industry ? `<div class="result-snippet industry-muted">${esc(r.industry).substring(0, 160)}${r.industry.length > 160 ? '...' : ''}</div>` : ''}
                <div class="result-tags-inline">
                    ${status ? `<span class="result-status-text ${statusClass}">${esc(status)}</span>` : ''}
                    <span class="result-score-text">Độ phù hợp: ${pct}%</span>
                </div>
            </div>
        `;

        list.appendChild(card);
    });
    
    currentDisplayed = end;
    
    if (currentDisplayed < filteredResults.length) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// ============================================================================
// Advanced Features
// ============================================================================

function applyFilter() {
    const filterStatus = document.getElementById('status-filter').value;
    const pFilter = document.getElementById('province-filter');
    const filterProvince = pFilter ? pFilter.value : 'all';
    
    filteredResults = allResults.filter(r => {
        // Trạng thái (Status)
        const s = (r.status || '').toLowerCase();
        let passStatus = true;
        if (filterStatus === 'active') {
            passStatus = !s.includes('ngừng') && !s.includes('giải thể');
        } else if (filterStatus === 'inactive') {
            passStatus = s.includes('ngừng') || s.includes('giải thể');
        }
        
        // Tỉnh thành (Province)
        let passProvince = true;
        if (filterProvince !== 'all') {
            const p = extractProvince(r.address);
            passProvince = (p === filterProvince);
        }
        
        return passStatus && passProvince;
    });
    
    currentDisplayed = 0;
    document.getElementById('results-list').innerHTML = '';
    loadMore();
}

function copyMST(mst) {
    if (!mst || mst === 'N/A') return;
    navigator.clipboard.writeText(mst).then(() => {
        alert("Đã Copy Mã Số Thuế: " + mst);
    });
}



function exportToCSV() {
    if (!filteredResults || filteredResults.length === 0) {
        alert("Không có kết quả để xuất!");
        return;
    }
    
    const headers = ['Tên Doanh Nghiệp', 'Mã Số Thuế', 'Đại Diện', 'Địa Chỉ', 'Tình Trạng', 'Ngành Nghề'];
    let csvContent = "data:text/csv;charset=utf-8,\uFEFF" + headers.join(',') + "\n";
    
    filteredResults.forEach(r => {
        const row = [
            `"${(r.company_name||'').replace(/"/g, '""')}"`,
            `"${r.tax_code||''}"`,
            `"${(r.representative||'').replace(/"/g, '""')}"`,
            `"${(r.address||'').replace(/"/g, '""')}"`,
            `"${r.status||''}"`,
            `"${(r.industry||'').replace(/"/g, '""')}"`
        ];
        csvContent += row.join(',') + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Data_${currentQuery.substring(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showDetail(idx) {
    const r = filteredResults[idx];
    if (!r) return;
    
    document.getElementById('modal-title').textContent = r.company_name || 'Unnamed';
    
    let html = '<div class="modal-body-grid">';
    
    const fields = [
        { label: 'Mã số thuế', value: r.tax_code },
        { label: 'Đại diện', value: r.representative },
        { label: 'Trạng thái', value: r.status },
        { label: 'Địa chỉ', value: r.address },
        { label: 'Ngành nghề', value: r.industry }
    ];
    
    fields.forEach(f => {
        if (f.value) {
            html += `<div class="modal-label">${f.label}:</div>`;
            html += `<div class="modal-value">${esc(f.value)}</div>`;
        }
    });
    html += '</div>';
    
    document.getElementById('modal-body').innerHTML = html;
    document.getElementById('detail-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Khóa cuộn background
}

function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
    document.body.style.overflow = ''; // Mở lại cuộn background
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target == modal) {
        modal.style.display = "none";
        document.body.style.overflow = ''; // Mở lại cuộn background
    }
}

// ============================================================================
// Stats
// ============================================================================

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const s = await res.json();
        document.getElementById('stat-docs').textContent = fmt(s.total_documents);
        document.getElementById('stat-vocab').textContent = fmt(s.vocabulary_size);
        document.getElementById('stat-ai').textContent = s.vector_index_loaded ? 'Sẵn sàng ✓' : 'Chưa có';
    } catch (e) {
        console.error(e);
    }
}

// ============================================================================
// Utils
// ============================================================================

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function fmt(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
    return String(n);
}
