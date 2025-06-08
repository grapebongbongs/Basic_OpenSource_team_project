/* ------------------------------------------------------------------
   1) 높이를 ‘딱 한 번’만 계산하고 고정
------------------------------------------------------------------ */
function adjustAllParentsPrecisely(selector) {
    document.querySelectorAll(selector).forEach(parent => {

        /* 이미 고정돼 있으면 건너뛰기 -------------------------- */
        if (parent.dataset.heightFixed === 'true') return;

        let maxBottom = 0;
        const parentRect = parent.getBoundingClientRect();
        const parentScrollTop = parent.scrollTop;

        Array.from(parent.children).forEach(child => {
            const childRect = child.getBoundingClientRect();
            const bottom = childRect.bottom - parentRect.top + parentScrollTop;
            if (bottom > maxBottom) maxBottom = bottom;
        });

        /* 높이 고정 + 플래그 기록 ----------------------------- */
        parent.style.height = `${Math.ceil(maxBottom)}px`;
        parent.dataset.heightFixed = 'true';   // ← 한 번만 실행되도록 표시
    });
}

/* ------------------------------------------------------------------
   2) ‘페이지 로드’ 때만 실행  ― 새로고침·첫 진입 시점
------------------------------------------------------------------ */
window.addEventListener('load', () => {
    adjustAllParentsPrecisely('.div, .background, .container, .body');
});

/* resize 리스너 제거 ― 더 이상 필요 없음
window.addEventListener('resize', () => {
    adjustAllParentsPrecisely('.div, .background, .container, .body');
});
*/
